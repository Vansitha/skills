// Renders a glowing, sticker-eyed mascot from a JSON spec.
//
//   swiftc -O render.swift -o "$TMPDIR/mascot-render"
//   "$TMPDIR/mascot-render" spec.json out-dir [reference-image]
//
// Writes into out-dir:
//   icon.png       1024 x 1024, opaque, square corners (iOS masks it): ready for an AppIcon set
//   preview.png    the icon in an iOS-shaped mask with a soft outer glow, on white
//   character.png  the character alone on a transparent background, for use inside an app
//   compare.png    the reference beside the icon, when a reference image is given
//
// Every coordinate and length in the spec is in the spec's "space" (default 0-1024). When tracing a reference,
// set "space" to the icon's box in the reference's own pixels, then copy measurements straight in.
import CoreGraphics
import CoreImage
import Foundation
import ImageIO
import UniformTypeIdentifiers

typealias Dict = [String: Any]
let args = CommandLine.arguments
guard args.count >= 3 else {
    print("usage: render spec.json out-dir [reference-image]")
    exit(1)
}
let spec = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: args[1]))) as! Dict
let outDir = URL(fileURLWithPath: args[2], isDirectory: true)
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

// MARK: Units and colours

let N = 1024
let S = CGFloat(N)
let space = spec["space"] as? Dict ?? [:]
let sx = num(space, "x", 0), sy = num(space, "y", 0), ssize = num(space, "size", 1024)
let k = S / ssize
func num(_ d: Dict, _ key: String, _ fallback: CGFloat) -> CGFloat {
    if let n = d[key] as? NSNumber { return CGFloat(truncating: n) }
    return fallback
}
func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: (x - sx) * k, y: (y - sy) * k) }
func L(_ v: CGFloat) -> CGFloat { v * k }
let rgb = CGColorSpace(name: CGColorSpace.sRGB)!
func color(_ hex: Any?, _ alpha: CGFloat = 1) -> CGColor {
    var s = (hex as? String ?? "000000").trimmingCharacters(in: .whitespaces)
    if s.hasPrefix("#") { s.removeFirst() }
    let v = UInt32(s, radix: 16) ?? 0
    return CGColor(srgbRed: CGFloat((v >> 16) & 0xFF) / 255, green: CGFloat((v >> 8) & 0xFF) / 255,
                   blue: CGFloat(v & 0xFF) / 255, alpha: alpha)
}

// MARK: Canvas helpers

func canvas(_ n: Int, opaque: Bool) -> CGContext {
    let ctx = CGContext(data: nil, width: n, height: n, bitsPerComponent: 8, bytesPerRow: 0, space: rgb,
                        bitmapInfo: opaque ? CGImageAlphaInfo.noneSkipLast.rawValue : CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.translateBy(x: 0, y: CGFloat(n))
    ctx.scaleBy(x: 1, y: -1)   // y runs down, like design tools and image pixels
    return ctx
}
let ci = CIContext(options: [.workingColorSpace: rgb])
func blurred(_ image: CGImage, _ sigma: CGFloat) -> CGImage {
    guard sigma > 0 else { return image }
    let input = CIImage(cgImage: image)
    let out = input.clampedToExtent().applyingGaussianBlur(sigma: sigma).cropped(to: input.extent)
    return ci.createCGImage(out, from: input.extent)!
}
func place(_ ctx: CGContext, _ image: CGImage, _ rect: CGRect) {
    ctx.saveGState()
    ctx.translateBy(x: rect.minX, y: rect.maxY)
    ctx.scaleBy(x: 1, y: -1)
    ctx.draw(image, in: CGRect(origin: .zero, size: rect.size))
    ctx.restoreGState()
}
let full = CGRect(x: 0, y: 0, width: S, height: S)
/// Draws `body` into its own layer, blurs it, and lays it on `ctx` (optionally clipped to `clip`).
func softLayer(_ ctx: CGContext, blur: CGFloat, clip: CGPath? = nil, _ body: (CGContext) -> Void) {
    let layer = canvas(N, opaque: false)
    body(layer)
    let image = blurred(layer.makeImage()!, blur)
    ctx.saveGState()
    if let clip { ctx.addPath(clip); ctx.clip() }
    place(ctx, image, full)
    ctx.restoreGState()
}
func radial(_ ctx: CGContext, _ c: CGPoint, _ r: CGFloat, _ col: CGColor) {
    let g = CGGradient(colorsSpace: rgb, colors: [col, col.copy(alpha: 0)!] as CFArray, locations: [0, 1])!
    ctx.drawRadialGradient(g, startCenter: c, startRadius: 0, endCenter: c, endRadius: r, options: [])
}
func ellipse(_ c: CGPoint, _ rx: CGFloat, _ ry: CGFloat, _ degrees: CGFloat) -> CGPath {
    var t = CGAffineTransform(translationX: c.x, y: c.y).rotated(by: degrees * .pi / 180)
    return CGPath(ellipseIn: CGRect(x: -rx, y: -ry, width: rx * 2, height: ry * 2), transform: &t)
}
func save(_ image: CGImage, _ name: String) {
    let url = outDir.appendingPathComponent(name)
    let d = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(d, image, nil)
    CGImageDestinationFinalize(d)
    print("wrote", url.path)
}

// MARK: SVG path data (M L H V C S Q T Z, absolute and relative; arcs become straight lines)

func svgPath(_ d: String) -> CGPath {
    var tokens: [String] = []
    var number = ""
    func flush() { if !number.isEmpty { tokens.append(number); number = "" } }
    for ch in d {
        if ch.isLetter && ch != "e" && ch != "E" { flush(); tokens.append(String(ch)) }
        else if ch == "-" && !(number.last == "e" || number.last == "E") { flush(); number = "-" }
        else if ch == "." && number.contains(".") { flush(); number = "." }
        else if ch.isNumber || ch == "." || ch == "e" || ch == "E" { number.append(ch) }
        else { flush() }
    }
    flush()
    let path = CGMutablePath()
    var i = 0, cmd = "M"
    var cur = CGPoint.zero, start = CGPoint.zero, lastControl: CGPoint? = nil, lastWasQuad = false
    func next() -> CGFloat { defer { i += 1 }; return CGFloat(Double(tokens[i]) ?? 0) }
    func hasNumber() -> Bool { i < tokens.count && Double(tokens[i]) != nil }
    while i < tokens.count {
        if !hasNumber() { cmd = tokens[i]; i += 1 }
        let rel = cmd == cmd.lowercased() && cmd != "z"
        func pt() -> CGPoint { let x = next(), y = next(); return rel ? CGPoint(x: cur.x + x, y: cur.y + y) : CGPoint(x: x, y: y) }
        switch cmd.uppercased() {
        case "M":
            cur = pt(); start = cur; path.move(to: cur); lastControl = nil
            cmd = rel ? "l" : "L"   // further pairs are lines
        case "L": cur = pt(); path.addLine(to: cur); lastControl = nil
        case "H": let x = next(); cur = CGPoint(x: rel ? cur.x + x : x, y: cur.y); path.addLine(to: cur); lastControl = nil
        case "V": let y = next(); cur = CGPoint(x: cur.x, y: rel ? cur.y + y : y); path.addLine(to: cur); lastControl = nil
        case "C":
            let c1 = pt(), c2 = pt(), end = pt()
            path.addCurve(to: end, control1: c1, control2: c2); cur = end; lastControl = c2; lastWasQuad = false
        case "S":
            let c1 = (lastControl != nil && !lastWasQuad) ? CGPoint(x: 2 * cur.x - lastControl!.x, y: 2 * cur.y - lastControl!.y) : cur
            let c2 = pt(), end = pt()
            path.addCurve(to: end, control1: c1, control2: c2); cur = end; lastControl = c2; lastWasQuad = false
        case "Q":
            let c = pt(), end = pt()
            path.addQuadCurve(to: end, control: c); cur = end; lastControl = c; lastWasQuad = true
        case "T":
            let c = (lastControl != nil && lastWasQuad) ? CGPoint(x: 2 * cur.x - lastControl!.x, y: 2 * cur.y - lastControl!.y) : cur
            let end = pt()
            path.addQuadCurve(to: end, control: c); cur = end; lastControl = c; lastWasQuad = true
        case "A":
            _ = next(); _ = next(); _ = next(); _ = next(); _ = next()
            cur = pt(); path.addLine(to: cur); lastControl = nil
        case "Z":
            path.closeSubpath(); cur = start; lastControl = nil
        default:
            i += 1
        }
    }
    var t = CGAffineTransform(translationX: -sx * k, y: -sy * k).scaledBy(x: k, y: k)
    return path.copy(using: &t)!
}

// MARK: Shapes

func drawBody(_ ctx: CGContext, _ s: Dict) {
    let path = svgPath(s["path"] as? String ?? "")
    if let sh = s["shadow"] as? Dict {
        softLayer(ctx, blur: L(num(sh, "blur", 28))) { layer in
            layer.addPath(path)
            layer.setFillColor(color(sh["color"], num(sh, "alpha", 0.7)))
            layer.fillPath()
        }
    }
    ctx.saveGState()
    ctx.addPath(path)
    ctx.clip()
    if let g = s["gradient"] as? Dict {
        let box = path.boundingBox
        let grad = CGGradient(colorsSpace: rgb, colors: [color(g["top"]), color(g["bottom"])] as CFArray, locations: [0, 1])!
        ctx.drawLinearGradient(grad, start: CGPoint(x: box.midX, y: box.minY), end: CGPoint(x: box.midX, y: box.maxY), options: [])
    } else {
        ctx.setFillColor(color(s["fill"]))
        ctx.fill(full)
    }
    ctx.restoreGState()
    if let gl = s["glow"] as? Dict {
        softLayer(ctx, blur: L(num(gl, "blur", 15)), clip: path) { layer in
            layer.addPath(path)
            layer.setStrokeColor(color(gl["color"], num(gl, "alpha", 1)))
            layer.setLineWidth(L(num(gl, "width", 64)))
            layer.strokePath()
            for e in gl["extra"] as? [Dict] ?? [] {
                layer.setFillColor(color(e["color"] ?? gl["color"], num(e, "alpha", 0.5)))
                layer.addPath(ellipse(P(num(e, "x", 0), num(e, "y", 0)), L(num(e, "rx", 50)), L(num(e, "ry", 20)), num(e, "rotation", 0)))
                layer.fillPath()
            }
        }
    }
    if let rim = s["rim"] as? Dict {
        ctx.addPath(path)
        ctx.setStrokeColor(color(rim["color"], num(rim, "alpha", 0.9)))
        ctx.setLineWidth(L(num(rim, "width", 2.5)))
        ctx.strokePath()
    }
}

/// An eye: "open" (white, pupil, shine), "happy" (an upward arc), or "sleepy" / "closed" (a soft downward arc).
func drawEye(_ ctx: CGContext, _ s: Dict) {
    let c = P(num(s, "x", 512), num(s, "y", 512))
    let rx = L(num(s, "rx", 60)), ry = L(num(s, "ry", 90)), tilt = num(s, "tilt", 0)
    let style = s["style"] as? String ?? "open"
    let ink = color(s["ink"] ?? "030303")
    if style != "open" {
        // Narrower than the open eye, so two arcs side by side stay apart.
        let arc = CGMutablePath()
        let half = rx * 0.68
        let lift: CGFloat = style == "happy" ? -0.55 : 0.35
        arc.move(to: CGPoint(x: -half, y: style == "happy" ? ry * 0.12 : 0))
        arc.addQuadCurve(to: CGPoint(x: half, y: style == "happy" ? ry * 0.12 : 0), control: CGPoint(x: 0, y: ry * lift))
        var t = CGAffineTransform(translationX: c.x, y: c.y).rotated(by: tilt * .pi / 180)
        ctx.addPath(arc.copy(using: &t)!)
        ctx.setStrokeColor(ink)
        ctx.setLineWidth(rx * 0.3)
        ctx.setLineCap(.round)
        ctx.strokePath()
        return
    }
    ctx.addPath(ellipse(c, rx, ry, tilt))
    ctx.setFillColor(color(s["white"] ?? "FFFFFF"))
    ctx.fillPath()
    if let p = s["pupil"] as? Dict {
        ctx.addPath(ellipse(CGPoint(x: c.x + L(num(p, "dx", 0)), y: c.y + L(num(p, "dy", 0))), L(num(p, "rx", 40)), L(num(p, "ry", 60)), tilt))
        ctx.setFillColor(ink)
        ctx.fillPath()
    }
    if let sh = s["shine"] as? Dict {
        ctx.addPath(ellipse(CGPoint(x: c.x + L(num(sh, "dx", 0)), y: c.y + L(num(sh, "dy", 0))), L(num(sh, "rx", 12)), L(num(sh, "ry", 24)), tilt))
        ctx.setFillColor(color(sh["color"] ?? "FFFFFF"))
        ctx.fillPath()
    }
}

/// A flat ring (a halo) with an optional lighter stripe along its top.
func drawRing(_ ctx: CGContext, _ s: Dict) {
    let c = P(num(s, "x", 512), num(s, "y", 200))
    let rx = L(num(s, "rx", 180)), ry = L(num(s, "ry", 40)), rot = num(s, "rotation", 0), w = L(num(s, "width", 30))
    let ring = ellipse(c, rx, ry, rot)
    ctx.addPath(ring)
    ctx.setStrokeColor(color(s["color"] ?? "FFC618"))
    ctx.setLineWidth(w)
    ctx.strokePath()
    if let hl = s["highlight"] {
        ctx.saveGState()
        ctx.addPath(ring.copy(strokingWithWidth: w, lineCap: .round, lineJoin: .round, miterLimit: 1))
        ctx.clip()
        ctx.addPath(ellipse(CGPoint(x: c.x, y: c.y - w * 0.2), rx, ry, rot))
        ctx.setStrokeColor(color(hl, 0.9))
        ctx.setLineWidth(w * 0.3)
        ctx.strokePath()
        ctx.restoreGState()
    }
}

/// A plain ellipse (blush, a nose, a coin face), optionally blurred.
func drawEllipse(_ ctx: CGContext, _ s: Dict) {
    let shape = ellipse(P(num(s, "x", 512), num(s, "y", 512)), L(num(s, "rx", 20)), L(num(s, "ry", 20)), num(s, "rotation", 0))
    let fill = color(s["fill"] ?? "FFFFFF", num(s, "alpha", 1))
    let blur = L(num(s, "blur", 0))
    if blur > 0 {
        softLayer(ctx, blur: blur) { layer in layer.addPath(shape); layer.setFillColor(fill); layer.fillPath() }
    } else {
        ctx.addPath(shape); ctx.setFillColor(fill); ctx.fillPath()
    }
}

/// Any other path: a mouth, a tail, a prop. Filled, stroked, or both.
func drawPath(_ ctx: CGContext, _ s: Dict) {
    let path = svgPath(s["path"] as? String ?? "")
    if let f = s["fill"] {
        ctx.addPath(path); ctx.setFillColor(color(f, num(s, "alpha", 1))); ctx.fillPath()
    }
    if let st = s["stroke"] {
        ctx.addPath(path)
        ctx.setStrokeColor(color(st, num(s, "alpha", 1)))
        ctx.setLineWidth(L(num(s, "width", 8)))
        ctx.setLineCap(.round)
        ctx.setLineJoin(.round)
        ctx.strokePath()
    }
}

func drawShapes(_ ctx: CGContext) {
    for s in spec["shapes"] as? [Dict] ?? [] {
        switch s["type"] as? String {
        case "body": drawBody(ctx, s)
        case "eye": drawEye(ctx, s)
        case "ring": drawRing(ctx, s)
        case "ellipse": drawEllipse(ctx, s)
        case "path": drawPath(ctx, s)
        default: print("skipped a shape with no known type:", s["type"] ?? "none")
        }
    }
}

// MARK: Icon

let bg = spec["background"] as? Dict ?? [:]
let icon = canvas(N, opaque: true)
let fade = CGGradient(colorsSpace: rgb, colors: [color(bg["top"] ?? "2CB4FF"), color(bg["bottom"] ?? "06A0FF")] as CFArray, locations: [0, 1])!
icon.drawLinearGradient(fade, start: .zero, end: CGPoint(x: 0, y: S), options: [])
for g in bg["glows"] as? [Dict] ?? [] {
    radial(icon, P(num(g, "x", 512), num(g, "y", 512)), L(num(g, "r", 300)), color(g["color"], num(g, "alpha", 0.6)))
}
if let sp = bg["sparkles"] as? Dict {
    icon.setFillColor(color(sp["color"] ?? "FFFFFF", num(sp, "alpha", 0.85)))
    for dot in sp["dots"] as? [[NSNumber]] ?? [] where dot.count >= 3 {
        let c = P(CGFloat(truncating: dot[0]), CGFloat(truncating: dot[1])), r = L(CGFloat(truncating: dot[2]))
        icon.fillEllipse(in: CGRect(x: c.x - r, y: c.y - r, width: 2 * r, height: 2 * r))
    }
}
drawShapes(icon)
let iconImage = icon.makeImage()!
save(iconImage, "icon.png")

// MARK: Character alone

let alone = canvas(N, opaque: false)
drawShapes(alone)
save(alone.makeImage()!, "character.png")

// MARK: Preview

let pv = spec["preview"] as? Dict ?? [:]
let n = 1300
let pn = CGFloat(n)
let preview = canvas(n, opaque: true)
preview.setFillColor(color("FFFFFF"))
preview.fill(CGRect(x: 0, y: 0, width: pn, height: pn))
let box = CGRect(x: (pn - 920) / 2, y: (pn - 920) / 2, width: 920, height: 920)
let squircle = CGPath(roundedRect: box, cornerWidth: box.width * 0.225, cornerHeight: box.width * 0.225, transform: nil)
let glowColor = pv["glow"] ?? bg["bottom"] ?? "06A0FF"
preview.saveGState()
preview.setShadow(offset: CGSize(width: 0, height: 24), blur: 110, color: color(glowColor, 0.55))
preview.addPath(squircle)
preview.setFillColor(color(glowColor))
preview.fillPath()
preview.restoreGState()
preview.saveGState()
preview.addPath(squircle)
preview.clip()
place(preview, iconImage, box)
let rim = canvas(n, opaque: false)
rim.addPath(squircle)
rim.setStrokeColor(color(pv["rim"] ?? "FFFFFF", num(pv, "rimAlpha", 0.45)))
rim.setLineWidth(26)
rim.strokePath()
place(preview, blurred(rim.makeImage()!, 10), CGRect(x: 0, y: 0, width: pn, height: pn))
preview.restoreGState()
save(preview.makeImage()!, "preview.png")

// MARK: Compare

if args.count > 3 {
    let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[3]) as CFURL, nil)!
    let whole = CGImageSourceCreateImageAtIndex(src, 0, nil)!
    let crop = CGRect(x: sx, y: sy, width: ssize, height: ssize)
    let reference = whole.cropping(to: crop) ?? whole
    let pair = canvas(2 * N + 40, opaque: true)
    pair.setFillColor(color("FFFFFF"))
    pair.fill(CGRect(x: 0, y: 0, width: 2 * S + 40, height: 2 * S + 40))
    place(pair, reference, CGRect(x: 0, y: (S + 40) / 2, width: S, height: S))
    place(pair, iconImage, CGRect(x: S + 40, y: (S + 40) / 2, width: S, height: S))
    save(pair.makeImage()!, "compare.png")
}
