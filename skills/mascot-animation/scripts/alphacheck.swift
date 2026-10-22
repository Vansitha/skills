// Checks that a clip kept its transparent background: decodes it with AVFoundation, as an app will, looking at every
// 8th frame. Prints the most opaque corner (should be 0) and the most opaque pixel anywhere (should be about 255).
// Looking across the clip matters: an entrance's first frames are empty.
//
//   swiftc -O alphacheck.swift -o "$TMPDIR/mascot-alphacheck" && "$TMPDIR/mascot-alphacheck" clip.mov
// encode.sh runs it after every ios encode.
import AVFoundation
import CoreVideo

let asset = AVURLAsset(url: URL(fileURLWithPath: CommandLine.arguments[1]))
let semaphore = DispatchSemaphore(value: 0)
Task {
    defer { semaphore.signal() }
    guard let track = try await asset.loadTracks(withMediaType: .video).first else { print("no video track"); return }
    let reader = try AVAssetReader(asset: asset)
    let output = AVAssetReaderTrackOutput(track: track, outputSettings: [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    ])
    reader.add(output)
    reader.startReading()
    var index = 0, checked = 0, corner: UInt8 = 0, most: UInt8 = 0, w = 0, h = 0
    while let sample = output.copyNextSampleBuffer() {
        defer { index += 1 }
        guard index % 8 == 0, let buffer = CMSampleBufferGetImageBuffer(sample) else { continue }
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        let base = CVPixelBufferGetBaseAddress(buffer)!.assumingMemoryBound(to: UInt8.self)
        let row = CVPixelBufferGetBytesPerRow(buffer)
        w = CVPixelBufferGetWidth(buffer); h = CVPixelBufferGetHeight(buffer)
        corner = max(corner, base[3], base[(h - 1) * row + (w - 1) * 4 + 3])
        for y in stride(from: 0, to: h, by: 4) {
            for x in stride(from: 0, to: w, by: 4) { most = max(most, base[y * row + x * 4 + 3]) }
        }
        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
        checked += 1
    }
    let ok = corner == 0 && most > 200
    print("alpha \(ok ? "kept" : "LOST"): \(w)x\(h), \(checked) of \(index) frames checked, corner alpha \(corner), most opaque \(most)")
}
semaphore.wait()
