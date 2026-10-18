// Reads a reference image's pixels, so shapes and colours can be traced instead of guessed.
//
//   swiftc -O measure.swift -o "$TMPDIR/mascot-measure"
//   "$TMPDIR/mascot-measure" size   image.png
//   "$TMPDIR/mascot-measure" sample image.png x,y x,y ...    the hex colour at each point
//   "$TMPDIR/mascot-measure" row    image.png y [x0 x1]      where the colour changes along a row
//   "$TMPDIR/mascot-measure" col    image.png x [y0 y1]      where the colour changes down a column
//
// Coordinates are the image's own pixels, x right and y down. A change is a jump of more than 60 in R+G+B
// between pixels 4 apart: an edge. Each change prints as position:colour-after-the-edge.
import CoreGraphics
import Foundation
import ImageIO

let args = CommandLine.arguments
guard args.count >= 3 else {
    print("usage: measure size|sample|row|col image ...")
    exit(1)
}
let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[2]) as CFURL, nil)!
let image = CGImageSourceCreateImageAtIndex(src, 0, nil)!
let w = image.width, h = image.height
let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                    space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
let data = ctx.data!.assumingMemoryBound(to: UInt8.self)
func px(_ x: Int, _ y: Int) -> (Int, Int, Int) {
    let i = (min(max(y, 0), h - 1) * w + min(max(x, 0), w - 1)) * 4
    return (Int(data[i]), Int(data[i + 1]), Int(data[i + 2]))
}
func hex(_ c: (Int, Int, Int)) -> String { String(format: "%02X%02X%02X", c.0, c.1, c.2) }
func edges(_ points: [(Int, Int)]) -> [String] {
    guard var last = points.first.map({ px($0.0, $0.1) }) else { return [] }
    var out: [String] = []
    for (i, p) in points.enumerated() {
        let c = px(p.0, p.1)
        if abs(c.0 - last.0) + abs(c.1 - last.1) + abs(c.2 - last.2) > 60 {
            out.append("\(i == 0 ? 0 : (points[0].0 == p.0 ? p.1 : p.0)):\(hex(c))")
        }
        last = c
    }
    return out
}
let rest = args.dropFirst(3).map { Int($0) ?? 0 }
switch args[1] {
case "size":
    print("\(w) x \(h)")
case "sample":
    for p in args[3...] {
        let xy = p.split(separator: ",").compactMap { Int($0) }
        if xy.count == 2 { print(p, hex(px(xy[0], xy[1]))) }
    }
case "row":
    let y = rest.first ?? 0, x0 = rest.count > 2 ? rest[1] : 0, x1 = rest.count > 2 ? rest[2] : w
    print("y=\(y)", edges(stride(from: x0, to: x1, by: 4).map { ($0, y) }).joined(separator: " "))
case "col":
    let x = rest.first ?? 0, y0 = rest.count > 2 ? rest[1] : 0, y1 = rest.count > 2 ? rest[2] : h
    print("x=\(x)", edges(stride(from: y0, to: y1, by: 4).map { (x, $0) }).joined(separator: " "))
default:
    print("unknown command:", args[1])
}
