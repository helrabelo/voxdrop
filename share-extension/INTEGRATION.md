# Share Extension Integration Guide

> Technical details for integrating the Share Extension with VoxDrop Python app

## Communication Protocol

The Share Extension and Python app communicate via a shared App Group container using a file-based protocol.

### App Group Container Structure

```
~/Library/Group Containers/group.com.helrabelo.voxdrop/
├── pending/                    # Files waiting to be processed
│   └── {uuid}/                 # Job folder
│       ├── manifest.json       # Job metadata
│       └── audio/              # Audio files
│           ├── file1.opus
│           └── file2.opus
├── completed/                  # Processed results
│   └── {uuid}/
│       └── result.json         # Transcription result
└── status.json                 # Global status (optional)
```

### Manifest Format (pending/{uuid}/manifest.json)

```json
{
  "id": "uuid-string",
  "created_at": "2026-01-15T10:30:00Z",
  "source_app": "com.apple.finder",
  "files": [
    {
      "name": "WhatsApp Audio 2026-01-15.opus",
      "path": "audio/file1.opus",
      "size": 12345
    }
  ],
  "options": {
    "model": "base",
    "language": null
  }
}
```

### Result Format (completed/{uuid}/result.json)

```json
{
  "id": "uuid-string",
  "completed_at": "2026-01-15T10:31:00Z",
  "success": true,
  "transcription": "The transcribed text...",
  "error": null,
  "duration_seconds": 45.2,
  "model_used": "base"
}
```

## Swift Extension Implementation

### ShareViewController.swift

```swift
import Cocoa
import UniformTypeIdentifiers

class ShareViewController: NSViewController {

    private let appGroupID = "group.com.helrabelo.voxdrop"

    override var nibName: NSNib.Name? {
        return NSNib.Name("ShareViewController")
    }

    override func loadView() {
        super.loadView()
        processSharedItems()
    }

    private func processSharedItems() {
        guard let extensionContext = self.extensionContext else { return }
        guard let inputItems = extensionContext.inputItems as? [NSExtensionItem] else { return }

        let jobID = UUID().uuidString
        var audioFiles: [URL] = []

        let group = DispatchGroup()

        for item in inputItems {
            guard let attachments = item.attachments else { continue }

            for provider in attachments {
                // Check for audio types
                let audioTypes = [
                    UTType.audio,
                    UTType(filenameExtension: "opus"),
                    UTType(filenameExtension: "mp3"),
                    UTType(filenameExtension: "m4a"),
                    UTType(filenameExtension: "wav")
                ].compactMap { $0 }

                for audioType in audioTypes {
                    if provider.hasItemConformingToTypeIdentifier(audioType.identifier) {
                        group.enter()
                        provider.loadFileRepresentation(forTypeIdentifier: audioType.identifier) { url, error in
                            if let url = url {
                                audioFiles.append(url)
                            }
                            group.leave()
                        }
                        break
                    }
                }
            }
        }

        group.notify(queue: .main) {
            if audioFiles.isEmpty {
                self.showError("No audio files found")
                return
            }

            self.copyFilesToAppGroup(jobID: jobID, files: audioFiles)
        }
    }

    private func copyFilesToAppGroup(jobID: String, files: [URL]) {
        guard let containerURL = FileManager.default.containerURL(
            forSecurityApplicationGroupIdentifier: appGroupID
        ) else {
            showError("Cannot access App Group container")
            return
        }

        let jobURL = containerURL
            .appendingPathComponent("pending")
            .appendingPathComponent(jobID)
        let audioURL = jobURL.appendingPathComponent("audio")

        do {
            try FileManager.default.createDirectory(at: audioURL, withIntermediateDirectories: true)

            var fileManifest: [[String: Any]] = []

            for file in files {
                let destURL = audioURL.appendingPathComponent(file.lastPathComponent)
                try FileManager.default.copyItem(at: file, to: destURL)

                let attrs = try FileManager.default.attributesOfItem(atPath: destURL.path)
                let size = attrs[.size] as? Int ?? 0

                fileManifest.append([
                    "name": file.lastPathComponent,
                    "path": "audio/\(file.lastPathComponent)",
                    "size": size
                ])
            }

            // Write manifest
            let manifest: [String: Any] = [
                "id": jobID,
                "created_at": ISO8601DateFormatter().string(from: Date()),
                "source_app": Bundle.main.bundleIdentifier ?? "unknown",
                "files": fileManifest,
                "options": [
                    "model": "base",
                    "language": NSNull()
                ]
            ]

            let manifestData = try JSONSerialization.data(withJSONObject: manifest, options: .prettyPrinted)
            try manifestData.write(to: jobURL.appendingPathComponent("manifest.json"))

            // Success - close the extension
            self.extensionContext?.completeRequest(returningItems: nil)

        } catch {
            showError("Failed to process files: \(error.localizedDescription)")
        }
    }

    private func showError(_ message: String) {
        let error = NSError(domain: "VoxDrop", code: 1, userInfo: [
            NSLocalizedDescriptionKey: message
        ])
        self.extensionContext?.cancelRequest(withError: error)
    }
}
```

### Info.plist for Extension

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSExtension</key>
    <dict>
        <key>NSExtensionAttributes</key>
        <dict>
            <key>NSExtensionActivationRule</key>
            <string>SUBQUERY(
                extensionItems,
                $extensionItem,
                SUBQUERY(
                    $extensionItem.attachments,
                    $attachment,
                    ANY $attachment.registeredTypeIdentifiers UTI-CONFORMS-TO "public.audio"
                ).@count > 0
            ).@count > 0</string>
        </dict>
        <key>NSExtensionPointIdentifier</key>
        <string>com.apple.share-services</string>
        <key>NSExtensionPrincipalClass</key>
        <string>$(PRODUCT_MODULE_NAME).ShareViewController</string>
    </dict>
</dict>
</plist>
```

## Python App Integration

### File Watcher (Add to Python app)

```python
# voxdrop/watcher.py (future implementation)

import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

APP_GROUP_PATH = Path.home() / "Library/Group Containers/group.com.helrabelo.voxdrop"
PENDING_PATH = APP_GROUP_PATH / "pending"
COMPLETED_PATH = APP_GROUP_PATH / "completed"


class ShareExtensionHandler(FileSystemEventHandler):
    def __init__(self, transcribe_callback):
        self.transcribe_callback = transcribe_callback

    def on_created(self, event):
        if event.is_directory:
            return

        # Check for new manifest files
        if event.src_path.endswith("manifest.json"):
            self.process_job(Path(event.src_path).parent)

    def process_job(self, job_path: Path):
        manifest_path = job_path / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        job_id = manifest["id"]
        audio_files = [
            job_path / file["path"]
            for file in manifest["files"]
        ]

        # Transcribe
        try:
            text = self.transcribe_callback(
                audio_files,
                model=manifest["options"].get("model", "base"),
                language=manifest["options"].get("language"),
            )

            # Write result
            result_dir = COMPLETED_PATH / job_id
            result_dir.mkdir(parents=True, exist_ok=True)

            result = {
                "id": job_id,
                "completed_at": datetime.now().isoformat(),
                "success": True,
                "transcription": text,
                "error": None,
            }

            with open(result_dir / "result.json", "w") as f:
                json.dump(result, f, indent=2)

            # Cleanup pending
            shutil.rmtree(job_path)

        except Exception as e:
            # Write error result
            result = {
                "id": job_id,
                "completed_at": datetime.now().isoformat(),
                "success": False,
                "transcription": None,
                "error": str(e),
            }
            # ... write and cleanup


def start_watcher(transcribe_callback):
    """Start watching for Share Extension jobs."""
    PENDING_PATH.mkdir(parents=True, exist_ok=True)
    COMPLETED_PATH.mkdir(parents=True, exist_ok=True)

    handler = ShareExtensionHandler(transcribe_callback)
    observer = Observer()
    observer.schedule(handler, str(PENDING_PATH), recursive=True)
    observer.start()
    return observer
```

## Testing the Integration

### Manual Testing Steps

1. Build and install the Share Extension via Xcode
2. Start the Python VoxDrop app
3. Right-click an audio file in Finder
4. Select Share > VoxDrop
5. Verify file appears in App Group pending folder
6. Verify Python app processes and transcribes
7. Verify result appears in completed folder
8. Verify notification is sent

### Debugging

```bash
# View App Group container
open ~/Library/Group\ Containers/group.com.helrabelo.voxdrop/

# Watch for new files
fswatch -r ~/Library/Group\ Containers/group.com.helrabelo.voxdrop/pending/

# Check extension logs
log show --predicate 'subsystem == "com.helrabelo.voxdrop"' --last 1h
```

## Security Considerations

1. **Sandboxing**: Both the extension and main app run sandboxed
2. **App Groups**: Only apps with the same App Group entitlement can access the container
3. **File Validation**: Always validate audio files before processing
4. **Cleanup**: Remove processed files to prevent disk bloat
