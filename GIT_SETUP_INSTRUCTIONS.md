# Git Repository Setup Instructions - Windows 11

## 🎯 **Current Status**

✅ **Local Git Repository Created**: `D:\sanskrit-processor-lean\`  
✅ **Initial Commit Made**: Clean architecture with comprehensive commit message  
✅ **Functionality Tested**: Processes SRT files successfully  
✅ **Documentation Complete**: README, .gitignore, requirements.txt

## 🚀 **Next Steps: Push to Remote Repository**

Choose your preferred Windows 11 terminal environment:

### Option 1: GitHub (Recommended)

#### **Step 1: Create New GitHub Repository**
- Go to https://github.com/new
- Repository name: `sanskrit-processor-lean`
- Description: "Lean architecture for Sanskrit SRT processing - rebuilt from Post-Processing-Shruti"
- Choose Public or Private
- **DO NOT** initialize with README (we have one)

#### **Step 2: Push Using Your Preferred Terminal**

##### **A. Windows Command Prompt (cmd)**
```cmd
REM Navigate to the repository
cd D:\sanskrit-processor-lean

REM Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git

REM Push to GitHub
git push -u origin master
```

##### **B. PowerShell**
```powershell
# Navigate to the repository
Set-Location D:\sanskrit-processor-lean

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git

# Push to GitHub
git push -u origin master
```

##### **C. WSL2 Ubuntu Terminal**
```bash
# Navigate to the repository (note the WSL path)
cd /mnt/d/sanskrit-processor-lean

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git

# Push to GitHub
git push -u origin master
```

#### **Step 3: Verify Upload**
- Visit your GitHub repository
- Confirm all 14 files are present
- Check that README displays properly

### Option 2: GitLab

#### **Step 1: Create New GitLab Repository**
- Go to https://gitlab.com/projects/new
- Project name: `sanskrit-processor-lean`
- Choose visibility level

#### **Step 2: Push Using Your Preferred Terminal**

##### **A. Windows Command Prompt (cmd)**
```cmd
cd D:\sanskrit-processor-lean
git remote add origin https://gitlab.com/YOUR_USERNAME/sanskrit-processor-lean.git
git push -u origin master
```

##### **B. PowerShell**
```powershell
Set-Location D:\sanskrit-processor-lean
git remote add origin https://gitlab.com/YOUR_USERNAME/sanskrit-processor-lean.git
git push -u origin master
```

##### **C. WSL2 Ubuntu**
```bash
cd /mnt/d/sanskrit-processor-lean
git remote add origin https://gitlab.com/YOUR_USERNAME/sanskrit-processor-lean.git
git push -u origin master
```

### Option 3: Azure DevOps / Other Git Services

Follow the same pattern:
1. Create repository on your chosen platform
2. Use your preferred Windows terminal to add remote and push

## 🔄 **Repository Relationship**

```
Original: D:\Post-Processing-Shruti (preserved for reference)
├── 100+ files, 10,000+ lines
├── Complex architecture (over-engineered)
├── Import errors preventing execution
└── Valuable lexicons and feature identification

New Lean: D:\sanskrit-processor-lean (production ready)  
├── 7 core files, 500 lines
├── Clean architecture with external service integration
├── Fully functional end-to-end processing
└── All valuable features preserved
```

## 📋 **File Inventory in New Repository**

```
sanskrit-processor-lean/
├── README.md                    # Comprehensive documentation
├── requirements.txt             # Minimal dependencies  
├── .gitignore                  # Clean ignore rules
├── config.yaml                 # Simple configuration
├── sample_test.srt             # Test file
├── sanskrit_processor_v2.py    # Core processor (200 lines)
├── simple_cli.py               # Basic CLI interface
├── enhanced_processor.py       # MCP/API integration
├── enhanced_cli.py             # Full-featured CLI
├── lexicons/
│   ├── corrections.yaml        # 25 Sanskrit/Hindi corrections
│   └── proper_nouns.yaml      # 23 proper noun capitalizations
└── services/
    ├── __init__.py
    ├── mcp_client.py          # MCP integration with fallback
    └── api_client.py          # External API client
```

## 🎯 **Commit History**

The initial commit includes a comprehensive message documenting:
- Architectural transformation from original system
- Performance improvements (95% code reduction)
- Functionality verification (fully working vs broken original)
- Feature preservation (all valuable features maintained)

## 🚀 **Immediate Usage After Push**

Once pushed to remote, anyone can use immediately. **Choose your Windows terminal:**

### **Windows Command Prompt (cmd)**
```cmd
REM Clone the repository
git clone https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git
cd sanskrit-processor-lean

REM Install dependencies (optional - only PyYAML required for core)
pip install -r requirements.txt

REM Test immediately
python simple_cli.py sample_test.srt output.srt --lexicons lexicons
```

### **PowerShell**
```powershell
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git
Set-Location sanskrit-processor-lean

# Install dependencies (optional - only PyYAML required for core)  
pip install -r requirements.txt

# Test immediately
python simple_cli.py sample_test.srt output.srt --lexicons lexicons
```

### **WSL2 Ubuntu**
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sanskrit-processor-lean.git
cd sanskrit-processor-lean

# Install dependencies (optional - only PyYAML required for core)
pip install -r requirements.txt

# Test immediately  
python3 simple_cli.py sample_test.srt output.srt --lexicons lexicons
```

**Expected result in all cases**: 5 corrections applied in <0.01 seconds

## 🔒 **Preservation Strategy**

This approach gives you:

1. **Original Repository Untouched**: Complete history and reference preserved
2. **Clean New Repository**: Production-ready system with clear architecture
3. **Easy Comparison**: Can reference original for feature archeology
4. **Migration Path**: Clear upgrade path documented in README

## 💡 **Recommended Next Steps**

1. **Push to remote** (GitHub recommended for visibility)
2. **Update original repo README** to point to new lean architecture
3. **Archive original repo** (don't delete - keep for reference)
4. **Use new repo** for all active development

This strategy preserves your investment while providing a clean foundation for future work.