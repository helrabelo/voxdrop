# VoxDrop v0.4.0 Development Plan

## Current Issues to Fix

### 1. Paste from Clipboard Not Working
**Priority:** Critical

The paste feature stopped working after recent changes. Need to investigate:
- Check `app.py` for any broken code from the icon integration
- Verify the clipboard paste callback is still properly connected
- Test the `_paste_from_clipboard` method

### 2. Menu Bar Shows "VoxDrop" Text + Icon
**Priority:** High

Current: Shows both icon and "VoxDrop" text
Desired: Only show the waveform icon (no text)

Fix in `app.py`:
```python
super().__init__(
    name="VoxDrop",
    title=None,  # Should be None or empty string
    icon=icon_path,
    template=True,
    quit_button=None,
)
```

May need to verify rumps behavior - some versions require `title=""` instead of `title=None`.

### 3. Icon Backgrounds Need Removal
**Priority:** Medium

Both icons from Leonardo.ai have backgrounds that need to be removed:
- `assets/icon.png` - Has checkered/transparent background visible
- `assets/menubar_icon.png` - Has light gray background

Options:
1. Use remove.bg or similar tool
2. Re-generate with better prompts
3. Use Python/PIL to remove backgrounds programmatically

For menu bar icon specifically:
- Must be pure black/dark gray on transparent
- macOS template mode will invert colors automatically for dark menu bars

---

## New Features to Implement

### 4. Auto-Update System
**Priority:** High

#### 4.1 Check for Updates Feature
Add menu item "Check for Updates..." that:
1. Fetches latest release from GitHub API
2. Compares with current version
3. Shows dialog with update info
4. Opens download link in browser

```python
# GitHub API endpoint
RELEASES_API = "https://api.github.com/repos/helrabelo/voxdrop/releases/latest"

def _check_for_updates(self, _):
    """Check GitHub for new releases."""
    import urllib.request
    import json

    try:
        with urllib.request.urlopen(RELEASES_API) as response:
            data = json.loads(response.read())
            latest_version = data["tag_name"].lstrip("v")
            current_version = "0.4.0"  # from __init__.py

            if latest_version > current_version:
                # Show update available dialog
                # Open landing page or GitHub releases
            else:
                # Show "You're up to date" notification
    except Exception as e:
        notify_error(f"Could not check for updates: {e}")
```

#### 4.2 Update Notification on Launch
On app startup, silently check for updates and show notification if available:
- Only check once per day (store last check timestamp)
- Non-intrusive notification
- Link to download page

#### 4.3 Landing Page Links
Add menu items:
- "VoxDrop Website" → Opens landing page (voxdrop.vercel.app or custom domain)
- "View on GitHub" → Opens GitHub repo
- "Report Issue" → Opens GitHub issues

### 5. Version Display
Add version to the menu:
```
─────────────
VoxDrop v0.4.0
Check for Updates...
─────────────
```

---

## File Changes Required

### voxdrop/app.py
- [ ] Fix paste from clipboard functionality
- [ ] Fix menu bar title (icon only, no text)
- [ ] Add "Check for Updates..." menu item
- [ ] Add "VoxDrop Website" menu item
- [ ] Add version display in menu
- [ ] Add startup update check (with 24h cooldown)

### voxdrop/__init__.py
- [ ] Update version to 0.4.0

### assets/
- [ ] Fix icon.png (remove background)
- [ ] Fix menubar_icon.png (remove background, ensure pure dark gray on transparent)

### VoxDrop.spec
- [ ] Update version to 0.4.0

### Landing Page (voxdrop-site)
- [ ] Deploy to Vercel
- [ ] Get custom domain (optional: voxdrop.dev, voxdrop.app)
- [ ] Update download URLs after GitHub release

---

## Implementation Order

### Phase 1: Fix Critical Bugs
1. Debug and fix paste from clipboard
2. Fix menu bar to show icon only (no text)
3. Remove backgrounds from icons

### Phase 2: Add Update System
1. Add version display in menu
2. Implement "Check for Updates" feature
3. Add website/GitHub links to menu
4. Add startup update check with cooldown

### Phase 3: Build & Release
1. Update version to 0.4.0
2. Rebuild app with `./scripts/build.sh`
3. Create DMG with `./scripts/create-dmg.sh`
4. Test thoroughly

### Phase 4: Deploy & Publish
1. Deploy landing page to Vercel
2. Push code to GitHub
3. Create GitHub Release v0.4.0
4. Update landing page download URL

---

## Testing Checklist

- [ ] Paste from clipboard works (copy .opus file in Finder → paste in VoxDrop)
- [ ] Select Audio Files works
- [ ] Menu bar shows only icon (no text)
- [ ] Icon adapts to light/dark menu bar
- [ ] Check for Updates shows correct dialog
- [ ] Website link opens landing page
- [ ] History shows recent transcriptions
- [ ] Model selection works
- [ ] Language selection works
- [ ] Launch at Login toggle works

---

## URLs to Configure

```
LANDING_PAGE_URL = "https://voxdrop.vercel.app"  # Update after deploy
GITHUB_URL = "https://github.com/helrabelo/voxdrop"
RELEASES_URL = "https://github.com/helrabelo/voxdrop/releases"
ISSUES_URL = "https://github.com/helrabelo/voxdrop/issues"
RELEASES_API = "https://api.github.com/repos/helrabelo/voxdrop/releases/latest"
```

---

## Notes

- The menu bar icon must be a "template image" for macOS - pure black/gray on transparent background
- rumps `template=True` handles light/dark mode automatically
- GitHub API is rate-limited (60 requests/hour for unauthenticated) - sufficient for update checks
- Consider Sparkle framework for future if more sophisticated updates needed
