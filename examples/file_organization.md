# Recipe: Organize Downloads by file type

**Prompt** (paste into Claude Code with Seer + filesystem MCPs installed):

```
Use the filesystem tool to list everything in C:\Users\<your-username>\Downloads.

Then sort each file into a subfolder based on extension:
  - Images: .png, .jpg, .jpeg, .gif, .webp, .svg → Downloads\Images\
  - Documents: .pdf, .docx, .doc, .txt, .md → Downloads\Documents\
  - Spreadsheets: .xlsx, .xls, .csv → Downloads\Spreadsheets\
  - Archives: .zip, .rar, .7z, .tar, .gz → Downloads\Archives\
  - Code: .py, .js, .ts, .json, .yaml → Downloads\Code\
  - Installers: .exe, .msi → Downloads\Installers\
  - Anything else: leave in place

Create the subfolders if they don't exist. Move each file using the filesystem tool. Don't touch any folder that's already a subfolder of Downloads. Show me a summary when done.
```

**What happens:**

1. Filesystem MCP lists files
2. Agent classifies each by extension
3. Filesystem MCP moves files (or seer drives File Explorer if filesystem MCP isn't installed)

**Where Seer fits:** if you don't have the filesystem MCP installed, the same prompt works — agent uses Seer's UIA tools to drive File Explorer instead. Slower but works.

**Variations to try:**
- "Sort by date instead of extension"
- "Move everything older than 30 days to Downloads\Archive\"
- "First show me what you would do, then ask before moving anything"
