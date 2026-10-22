# Shipping the clips

## Sizes

The clip's frame is `camera.frame / 2` times wider than the mascot (2.33 by default), so a hop or a turn fits inside it. Lay out the mascot's own size in the UI, then draw the clip centred on it, larger and unclipped.

| The mascot on screen | Clip box | Render at (3× screen) |
|---|---|---|
| 24 pt (an inline spinner) | 56 pt | 168 px |
| 40 pt (a toast or a hint) | 93 pt | 280 px |
| 60 pt (an empty state) | 140 pt | 420 px |
| 120 pt (an onboarding hero) | 280 pt | 840 px |
| Full screen (an entrance) | the screen | the screen in pixels, e.g. 1080x2340 |

The HEVC bitrate scales with the area: about 900 kbit/s at 300 px, giving about 150 KB for a 1 s clip, capped at 4 Mbit/s. A set of seven reactions at 300 px is about 1.4 MB.

## iOS and macOS (SwiftUI)

HEVC with alpha plays in `AVPlayerLayer`, but only if you ask for BGRA pixel buffers. Otherwise the transparency turns black. Play a clip only once it's ready and on screen, or a short reaction can start halfway through or finish unseen.

Show the last frame (the `.png`) as a placeholder until then, and under Reduce Motion. The exceptions are `entrance` and `peek`, which start with the mascot out of frame: the last frame would flash in its place and then vanish as the clip starts. Set `placeholder: false` for those, so the PNG shows only under Reduce Motion. `exit` ends out of frame, so remove the view when it finishes.

```swift
import AVFoundation
import SwiftUI
import UIKit

/// A mascot reaction: `size` is the mascot's own size; the clip is drawn `frameRatio` times larger around it, unclipped.
struct MascotClip: View {
    let name: String            // "hop" → hop.mov and hop.png in the bundle
    let size: CGFloat
    var loops = false
    var placeholder = true      // false for clips that start out of frame (entrance, peek)
    static let frameRatio: CGFloat = 4.66 / 2
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Color.clear
            .frame(width: size, height: size)
            .overlay {
                Group {
                    if reduceMotion, let still = UIImage(named: name) {
                        Image(uiImage: still).resizable()
                    } else {
                        ClipPlayer(url: Bundle.main.url(forResource: name, withExtension: "mov"), loops: loops,
                                   still: placeholder ? UIImage(named: name) : nil)
                    }
                }
                .frame(width: size * Self.frameRatio, height: size * Self.frameRatio)
                .allowsHitTesting(false)
            }
            .accessibilityHidden(true)
    }
}

private struct ClipPlayer: UIViewRepresentable {
    let url: URL?
    let loops: Bool
    let still: UIImage?
    func makeUIView(context: Context) -> ClipView { ClipView(url: url, loops: loops, still: still) }
    func updateUIView(_ view: ClipView, context: Context) {}
    static func dismantleUIView(_ view: ClipView, coordinator: ()) { view.stop() }
}

final class ClipView: UIView {
    override class var layerClass: AnyClass { AVPlayerLayer.self }
    private var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }
    private var looper: AVPlayerLooper?
    private var starting: Task<Void, Never>?
    private let placeholder: UIImageView

    init(url: URL?, loops: Bool, still: UIImage?) {
        placeholder = UIImageView(image: still)
        super.init(frame: .zero)
        backgroundColor = .clear
        isOpaque = false
        placeholder.contentMode = .scaleAspectFit
        addSubview(placeholder)
        playerLayer.videoGravity = .resizeAspect
        playerLayer.pixelBufferAttributes = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        guard let url else { return }
        let player: AVPlayer
        if loops {
            let queue = AVQueuePlayer()
            looper = AVPlayerLooper(player: queue, templateItem: AVPlayerItem(url: url))
            player = queue
        } else {
            player = AVPlayer(url: url)
        }
        player.isMuted = true
        player.preventsDisplaySleepDuringVideoPlayback = false
        playerLayer.player = player
        starting = Task { [weak self] in await self?.start(player) }
    }

    required init?(coder: NSCoder) { fatalError() }

    private func start(_ player: AVPlayer) async {
        let deadline = ContinuousClock.now + .seconds(2)
        while player.currentItem?.status != .readyToPlay {
            guard player.currentItem?.status != .failed, ContinuousClock.now < deadline, !Task.isCancelled else { return }
            try? await Task.sleep(for: .milliseconds(16))
        }
        await withCheckedContinuation { done in player.preroll(atRate: 1) { _ in done.resume() } }
        while window == nil || !playerLayer.isReadyForDisplay {
            guard ContinuousClock.now < deadline, !Task.isCancelled else { return }
            try? await Task.sleep(for: .milliseconds(16))
        }
        player.play()
        placeholder.isHidden = true
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        placeholder.frame = bounds
    }

    func stop() {
        starting?.cancel()
        playerLayer.player?.pause()
        looper = nil
        playerLayer.player = nil
    }
}
```

To replay a reaction, give the view a new identity: `.id(eventID)`. Fire the haptic on the landing frame, about 0.6 s into `hop`, with `.sensoryFeedback`.

## The web

Safari plays HEVC with alpha; Chrome, Firefox and Edge play WebM (VP9) with alpha. List the HEVC first, because Safari also claims WebM but drops its alpha:

```html
<video class="mascot" autoplay muted playsinline loop poster="idle.png" width="280" height="280">
  <source src="idle.mov" type='video/quicktime; codecs="hvc1"'>
  <source src="idle.webm" type="video/webm">
</video>
```

- Leave out `loop` for a reaction, and call `video.currentTime = 0; video.play()` to replay it.
- Under `prefers-reduced-motion: reduce`, show the poster PNG instead.
- In React, set `muted` as a property after mount if autoplay fails.

## Android

WebM with alpha plays in a WebView. For native views, the most reliable route is the PNG frames as an animated WebP (`ffmpeg -i f_%04d.png -loop 0 -lossless 0 -q:v 80 out.webp`), or a Lottie made by a designer. Video alpha support varies by device.

## Rules for using them

- **One mascot on screen at a time.** Each reaction plays at its spot and can be cut off by the next one.
- **Never block input,** and never make the user wait for a clip to finish.
- **The more often something happens, the smaller the motion.** A frequent action gets a quick hop. A rare milestone gets `celebrate`.
- **Keep text out of the clips,** in the UI's own type.
- **Under Reduce Motion, show the last frame,** with a short cross-fade if anything.
