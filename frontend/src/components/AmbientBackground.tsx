"use client";
import { motion } from "framer-motion";

const CONTOUR = [
  "M308 162 C 318 196, 352 238, 365 278 C 357 336, 352 378, 364 420 C 342 464, 288 530, 234 594 C 195 640, 178 696, 196 762",
  "M592 162 C 582 196, 548 238, 535 278 C 543 336, 548 378, 536 420 C 558 464, 612 530, 666 594 C 705 640, 722 696, 704 762",
  "M196 762 Q 450 796 704 762",
  "M308 162 C 355 145, 390 222, 450 232 C 510 222, 545 145, 592 162",
];

const SECTIONS = [
  { d: "M388 228 Q 450 240 512 228",   opacity: 0.18, dur: 7.0 },
  { d: "M330 286 Q 450 302 570 286",   opacity: 0.22, dur: 5.5 },
  { d: "M334 336 Q 450 353 566 336",   opacity: 0.22, dur: 6.2 },
  { d: "M344 386 Q 450 403 556 386",   opacity: 0.22, dur: 4.8 },
  { d: "M365 420 Q 450 432 535 420",   opacity: 0.24, dur: 7.5 },
  { d: "M348 470 Q 450 486 552 470",   opacity: 0.24, dur: 5.2 },
  { d: "M322 528 Q 450 548 578 528",   opacity: 0.24, dur: 6.8 },
  { d: "M292 588 Q 450 612 608 588",   opacity: 0.22, dur: 4.5 },
  { d: "M258 648 Q 450 675 642 648",   opacity: 0.22, dur: 7.2 },
  { d: "M224 706 Q 450 736 676 706",   opacity: 0.18, dur: 5.8 },
  { d: "M196 762 Q 450 796 704 762",   opacity: 0.16, dur: 6.5 },
];

const DRAPES = [
  { d: "M408 422 C 396 498, 368 576, 330 652 C 308 704, 272 740, 248 762", dur: 9 },
  { d: "M450 422 C 448 504, 444 584, 440 666 C 438 712, 436 742, 436 762", dur: 7 },
  { d: "M492 422 C 504 498, 532 576, 570 652 C 592 704, 628 740, 652 762", dur: 11 },
];

export default function AmbientBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 overflow-hidden"
      style={{ zIndex: 0 }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="100 80 700 780"
        preserveAspectRatio="xMidYMid meet"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Scale up dress width */}
        <g transform="translate(450 450) scale(1.55 1.1) translate(-450 -450)">

          {/* Outer silhouette — slow fade in/out */}
          {CONTOUR.map((d, i) => (
            <motion.path
              key={`c${i}`}
              d={d}
              stroke="#000"
              strokeWidth="1.2"
              strokeLinecap="round"
              strokeDasharray="2 8"
              animate={{ opacity: [0, 0.28, 0.28, 0.14, 0, 0.28] }}
              transition={{
                duration: 8 + i * 2.5,
                delay: i * 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          ))}

          {/* Horizontal cross-sections — each fades independently */}
          {SECTIONS.map((s, i) => (
            <motion.path
              key={`s${i}`}
              d={s.d}
              stroke="#000"
              strokeWidth="1"
              strokeLinecap="round"
              strokeDasharray="2 8"
              animate={{
                opacity: [0, s.opacity, s.opacity, 0, 0],
                translateY: [0, 7, 0],
              }}
              transition={{
                opacity: {
                  duration: s.dur,
                  delay: i * 0.55,
                  repeat: Infinity,
                  ease: "easeInOut",
                },
                translateY: {
                  duration: s.dur * 2.2,
                  delay: i * 0.55,
                  repeat: Infinity,
                  ease: "easeInOut",
                  repeatType: "mirror",
                },
              }}
            />
          ))}

          {/* Vertical drape folds */}
          {DRAPES.map((drape, i) => (
            <motion.path
              key={`d${i}`}
              d={drape.d}
              stroke="#000"
              strokeWidth="0.8"
              strokeLinecap="round"
              strokeDasharray="1.5 10"
              animate={{ opacity: [0, 0.14, 0.14, 0, 0] }}
              transition={{
                duration: drape.dur,
                delay: 2 + i * 2.2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          ))}

        </g>
      </svg>
    </div>
  );
}
