# VoxDrop Share Extension

> Native macOS Share Extension for VoxDrop (Future Development)

## Overview

This directory contains the scaffold for a native macOS Share Extension that will allow users to transcribe audio files directly from the macOS share sheet (e.g., from Finder, WhatsApp, or other apps).

## Why Native?

Share Extensions on macOS **require native code** (Swift or Objective-C). They cannot be built purely in Python. This extension will act as a bridge between the macOS share sheet and the Python-based VoxDrop app.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      macOS Share Sheet                       │
│                    (Finder, WhatsApp, etc.)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              VoxDrop Share Extension (Swift)                 │
│                                                              │
│  1. Receives audio files from share sheet                    │
│  2. Copies files to App Group container                      │
│  3. Signals Python app via file watcher                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 App Group Container                          │
│  ~/Library/Group Containers/group.com.helrabelo.voxdrop/    │
│                                                              │
│  - pending/           ← Extension writes here                │
│  - completed/         ← Python writes results here           │
│  - status.json        ← Communication status                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              VoxDrop Python App (rumps)                      │
│                                                              │
│  1. Monitors App Group container for new files               │
│  2. Transcribes using Whisper                                │
│  3. Writes result to completed/ folder                       │
│  4. Sends notification                                       │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

Before building the Share Extension:

1. **Apple Developer Account** - Required for code signing
2. **Xcode 15+** - For building the Swift extension
3. **App Groups Entitlement** - Must be configured in both apps
4. **Code Signing Certificates** - Developer ID or App Store certificates

## Building the Extension

### Step 1: Create Xcode Project

```bash
# Open Xcode and create new project:
# - macOS > App
# - Product Name: VoxDropShare
# - Team: Your Apple Developer Team
# - Bundle Identifier: com.helrabelo.voxdrop

# Then add Share Extension target:
# - File > New > Target > macOS > Share Extension
# - Product Name: VoxDropShareExtension
```

### Step 2: Configure App Groups

In both the main app and extension targets:

1. Go to **Signing & Capabilities**
2. Click **+ Capability**
3. Add **App Groups**
4. Create group: `group.com.helrabelo.voxdrop`

### Step 3: Implement Extension

See `INTEGRATION.md` for the Swift implementation details.

### Step 4: Build & Sign

```bash
# Build for testing
xcodebuild -scheme VoxDropShare -configuration Debug

# Build for distribution
xcodebuild -scheme VoxDropShare -configuration Release
```

## File Structure (To Be Created)

```
share-extension/
├── README.md                     # This file
├── INTEGRATION.md                # Implementation details
└── VoxDropShare/                 # Xcode project (create manually)
    ├── VoxDropShare.xcodeproj/
    ├── VoxDropShare/             # Main app (minimal, just for hosting)
    │   ├── VoxDropShareApp.swift
    │   └── ContentView.swift
    ├── VoxDropShareExtension/    # Share Extension
    │   ├── ShareViewController.swift
    │   ├── Info.plist
    │   └── VoxDropShareExtension.entitlements
    └── Shared/
        └── AppGroupConfig.swift  # Shared constants
```

## Development Status

- [ ] Create Xcode project
- [ ] Implement ShareViewController
- [ ] Configure App Groups
- [ ] Implement file monitoring in Python app
- [ ] Test end-to-end flow
- [ ] Code sign for distribution

## Timeline

This is planned for a future release after the Python MVP is stable. The priority is:

1. ✅ MVP with file picker (v0.1)
2. ✅ History and progress (v0.2)
3. 🔜 Share Extension (v0.3 or later)

## Resources

- [App Extension Programming Guide](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/)
- [Sharing Data with App Groups](https://developer.apple.com/documentation/xcode/configuring-app-groups)
- [NSItemProvider Documentation](https://developer.apple.com/documentation/foundation/nsitemprovider)
