# OpenClaw VPS Installation Guide

**Purpose:** Transform VPS from passive receiver to autonomous agent host

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| OS | Windows Server 2019+ |
| Access | Administrator RDP/SSH |
| RAM | 2GB+ available |
| Storage | 1GB+ free |

---

## Step 1: Install Node.js (Required)

### Download Node.js LTS
```
URL: https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi
```

### Install via PowerShell (Admin)
```powershell
# Download
Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi" -OutFile "$env:TEMP\node.msi"

# Install (silent)
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $env:TEMP\node.msi /qn" -Wait

# Verify
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

### Or use Chocolatey (if available)
```powershell
choco install nodejs-lts -y
```

---

## Step 2: Install OpenClaw

```powershell
# Install globally
npm install -g openclaw@latest

# Verify installation
openclaw --version
```

Expected output:
```
OpenClaw v2026.2.15
```

---

## Step 3: Configure OpenClaw

### Initialize configuration
```powershell
cd C:\Projects
openclaw configure
```

### Configuration Options

**Option A: Use Existing Local Workspace (Recommended)**
```powershell
# Mount local workspace via network share
# On local machine: Share ~/.openclaw/workspace as xkg_workspace

# On VPS:
net use Z: \\LOCAL_IP\xkg_workspace /user:username password

# Configure OpenClaw to use network share
openclaw config set workspace.path "Z:\.openclaw\workspace"
```

**Option B: Clone Repository**
```powershell
# Clone your workspace repo
cd C:\
git clone https://github.com/yourusername/openclaw-workspace.git
openclaw config set workspace.path "C:\openclaw-workspace"
```

**Option C: Separate Workspace**
```powershell
# Create dedicated workspace
mkdir C:\OpenClaw\Workspace
openclaw config set workspace.path "C:\OpenClaw\Workspace"
```

---

## Step 4: Configure Services

### Gmail (for notifications)
```powershell
openclaw config set gmail.user "griptoad.26@gmail.com"
openclaw config set gmail.refresh_token "YOUR_GMAIL_REFRESH_TOKEN"
```

### SSH Keys (for local machine access)
```powershell
# Copy SSH keys for GitHub/GitLab access
# Place in C:\Users\Administrator\.ssh\
```

### Antfarm
```powershell
cd C:\OpenClaw\Workspace
git clone https://github.com/openclaw/antfarm.git
cd antfarm
npm install
```

---

## Step 5: Install VPS Agent Workflows

Create `C:\OpenClaw\Workspace\agents\vps-agents.ps1`:

```powershell
#!/usr/bin/env pwsh
# VPS Autonomous Agent Controller

$PROJECT_PATH = "C:\Projects\x-knowledge-graph"
$LOG_PATH = "C:\OpenClaw\Workspace\logs"

# Ensure log directory exists
if (!(Test-Path $LOG_PATH)) {
    New-Item -ItemType Directory -Force -Path $LOG_PATH
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Tee-Object -FilePath "$LOG_PATH\vps-agents.log"
}

# Health Monitor (runs every 30 seconds)
function Start-HealthMonitor {
    while ($true) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:51338" -TimeoutSec 5 -ErrorAction SilentlyContinue
            
            if ($response.StatusCode -eq 200) {
                Write-Log "OK - Server responding (HTTP $($response.StatusCode))"
            }
            else {
                Write-Log "ERROR - Server returned $($response.StatusCode)"
                Restart-Server
            }
        }
        catch {
            Write-Log "ERROR - Server not responding: $($_.Exception.Message)"
            Restart-Server
        }
        
        Start-Sleep -Seconds 30
    }
}

# Auto-Deploy (runs every 5 minutes)
function Start-AutoDeploy {
    $LAST_VERSION = $null
    
    while ($true) {
        try {
            $localVersion = Get-Content "$PROJECT_PATH\VERSION.txt" -ErrorAction SilentlyContinue
            
            if ($LAST_VERSION -and $localVersion -ne $LAST_VERSION) {
                Write-Log "New version detected: $localVersion"
                Deploy-Update
            }
            
            $LAST_VERSION = $localVersion
        }
        catch {
            Write-Log "ERROR - Version check failed: $($_.Exception.Message)"
        }
        
        Start-Sleep -Seconds 300  # 5 minutes
    }
}

# Deploy Update
function Deploy-Update {
    Write-Log "Starting deployment..."
    
    # Stop current server
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Build (if on local machine/network)
    # Copy new files to VPS
    
    # Start server
    Set-Location $PROJECT_PATH
    $process = Start-Process -FilePath "python" -ArgumentList "main.py --port 51338" -PassThru -WindowStyle Hidden
    
    Start-Sleep -Seconds 5
    
    # Verify
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:51338" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "Deployment successful"
        }
    }
    catch {
        Write-Log "ERROR - Deployment verification failed"
    }
}

# Restart Server
function Restart-Server {
    Write-Log "Restarting server..."
    
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    Set-Location $PROJECT_PATH
    $process = Start-Process -FilePath "python" -ArgumentList "main.py --port 51338" -PassThru -WindowStyle Hidden
    
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:51338" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "Server restarted successfully"
        }
    }
    catch {
        Write-Log "ERROR - Server restart failed"
    }
}

# Start all agents
Write-Log "Starting VPS agents..."
Start-Job -ScriptBlock { & "$PSScriptRoot\Start-HealthMonitor" }
Start-Job -ScriptBlock { & "$PSScriptRoot\Start-AutoDeploy" }
```

### Register as Windows Service
```powershell
# Install NSSM (Non-Sucking Service Manager)
choco install nssm -y

# Create service
nssm install OpenClawVPSAgents "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
nssm set OpenClawVPSAgents AppParameters "-ExecutionPolicy Bypass -File C:\OpenClaw\Workspace\agents\vps-agents.ps1"
nssm set OpenClawVPSAgents AppDirectory "C:\OpenClaw\Workspace\agents"
nssm set OpenClawVPSAgents DisplayName "OpenClaw VPS Agents"
nssm set OpenClawVPSAgents Description "Autonomous agents for XKG health monitoring and auto-deploy"
nssm set OpenClawVPSAgents Start SERVICE_AUTO_START

# Start service
nssm start OpenClawVPSAgents

# Verify
nssm status OpenClawVPSAgents
```

---

## Step 6: Configure Firewall

```powershell
# Allow OpenClaw port (if different from 51338)
New-NetFirewallRule -DisplayName "OpenClaw" -Direction Inbound -Protocol TCP -LocalPort 51339 -Action Allow

# Allow Node.js
New-NetFirewallRule -DisplayName "Node.js" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
```

---

## Step 7: Verify Installation

```powershell
# Check OpenClaw
openclaw status

# Check antfarm
cd C:\OpenClaw\Workspace\antfarm
node dist/cli/cli.js dashboard start

# Check service
nssm status OpenClawVPSAgents

# Check logs
Get-Content C:\OpenClaw\Workspace\logs\vps-agents.log -Tail 20
```

---

## Step 8: Connect Local and VPS (Optional)

### Option A: Git Sync
```powershell
# Both machines sync to same Git repository

# Local:
cd ~/.openclaw/workspace
git add .
git commit -m "Update"
git push

# VPS:
cd C:\OpenClaw\Workspace
git pull
```

### Option B: Network Share
```powershell
# Mount local workspace on VPS
net use Z: \\LOCAL_MACHINE_IP\openclaw_workspace /user:username password

# Configure OpenClaw to use Z: drive
openclaw config set workspace.path "Z:\.openclaw\workspace"
```

---

## Daily Workflow

### On VPS (Autonomous)
```
• Health monitor runs every 30 seconds
• Auto-deploy checks every 5 minutes
• Logs written to C:\OpenClaw\Workspace\logs\
• Service runs in background (survives reboot)
```

### On Local Machine
```
• Development work
• git push changes
• Manual deploy (if needed): ssh VPS "cd C:\Projects\x-knowledge-graph && git pull"
```

---

## Troubleshooting

### OpenClaw won't start
```powershell
# Check Node.js
node --version

# Reinstall OpenClaw
npm uninstall -g openclaw
npm install -g openclaw@latest

# Check permissions
whoami
```

### Service won't start
```powershell
# Check NSSM
nssm restart OpenClawVPSAgents

# Check event logs
Get-EventLog -LogName Application -EntryType Error -Newest 10

# Check PowerShell execution policy
Set-ExecutionPolicy RemoteSigned -Scope Process -Force
```

### Server won't respond
```powershell
# Check Python processes
Get-Process -Name python*

# Check port binding
netstat -ano | findstr 51338

# Check firewall
Get-NetFirewallRule -DisplayName "xkg_51338"
```

### Git sync issues
```powershell
# Check SSH agent
Get-Service ssh-agent | Start-Service
ssh-add C:\Users\Administrator\.ssh\id_rsa

# Verify remote
git remote -v
git fetch origin
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `openclaw status` | Check OpenClaw status |
| `openclaw config get` | View configuration |
| `nssm start OpenClawVPSAgents` | Start agents |
| `nssm stop OpenClawVPSAgents` | Stop agents |
| `nssm restart OpenClawVPSAgents` | Restart agents |
| `Get-Content logs\vps-agents.log -Tail 50` | View logs |

---

## Files Created

```
C:\OpenClaw\Workspace\
├── agents/
│   └── vps-agents.ps1      # Agent controller script
├── logs/
│   └── vps-agents.log      # Agent activity log
├── config/
│   └── openclaw.yaml        # OpenClaw configuration
└── antfarm/                # Antfarm installation

C:\Projects\x-knowledge-graph\
├── main.py                 # XKG server
├── VERSION.txt             # Current version
└── distributions/          # Build artifacts
```

---

## Next Steps

1. Install Node.js on VPS
2. Install OpenClaw: `npm install -g openclaw@latest`
3. Configure workspace (git clone or network share)
4. Install NSSM: `choco install nssm`
5. Create agent script and service
6. Verify with `openclaw status`
7. Test health monitoring

Ready to proceed with installation on the VPS?
