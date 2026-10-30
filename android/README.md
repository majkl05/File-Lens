# FileLens for Android

Native Kotlin implementation, separate from the Windows/Python application.

## MVP

- Select multiple PDF files using Android Storage Access Framework.
- Persist read access to selected files.
- Extract PDF text locally using PDFBox-Android.
- Store page text in a private SQLite FTS4 full-text index.
- Search all query terms with AND semantics.
- Tap a result to open its PDF in an installed viewer.

Scanned/image-only PDFs are not OCR-processed yet. Pages without extractable text are skipped.

## Build

Requirements: JDK 17, Android SDK 35 and Gradle 8.9 or newer.

From the repository root run:

```bash
gradle assembleDebug
```

The APK is generated at `app/build/outputs/apk/debug/app-debug.apk`.

Minimum Android version: Android 8.0 (API 26). Indexing and searching are local; documents are not uploaded to a server.
