Below is a structured research digest you can use as a design reference when building a dependency-minimal, cross-platform, robust area-adjacency & gap-detection layer for Blender add-ons. I’ve organized it around your requested research areas and deliverables, and I close with concise answers to the Focus Questions.

0. Quick Orientation
When you look at on-screen “areas” in Blender (or any GUI), three coordinate domains typically interact:

Logical UI units (a.k.a. device-independent pixels, points, UI scale units).

Device pixels (hardware pixel grid; may be scaled by OS/toolkit).

Application pixels (what your app thinks a pixel is after applying its own scale settings; in Blender this involves ui_scale, DPI, pixel_size).

Robust adjacency detection depends on (a) consistently normalizing rectangles into a single working coordinate space, (b) understanding how rounding & scaling propagate error, and (c) using adaptive tolerances derived from the active scaling stack. The sections below build those pieces.

1. UI Scaling Principles (Cross-Framework Survey)
Key Pattern: Nearly all modern frameworks expose (or internally use) a logical coordinate space that’s scaled to device pixels by a per-monitor factor. Your code should obtain that factor (never hard-code) and do layout & hit-testing in logical space. Bitmaps or pixel-aligned drawing then multiply by the scale factor (often rounded). 
Qt ドキュメント
Microsoft Learn
Apple Developer

1.1 Windows (Win32 / Direct2D / XAML / WPF lineage)
Historically, Windows defined 1 logical inch = 96 “device-independent” pixels, so 12pt text → 16 logical px at 96 DPI; users can set system DPI (e.g., 125%, 150%), producing scaling relative to 96. Apps marked DPI-aware must recompute layout when DPI changes. 
Microsoft Learn

DPI Awareness Modes (Unaware, System, Per-Monitor, Per-Monitor V2) control whether Windows bitmap-scales you or sends WM_DPICHANGED so you can re-layout at the new DPI; PMv2 recommended. 
Microsoft Learn

Layout rounding (e.g., UIElement.UseLayoutRounding) snaps fractional layout metrics to whole device pixels to avoid blurry 1-px lines; default true in XAML. Useful concept to emulate when reconciling float rounding. 
Microsoft Learn

1.2 Qt
Qt operates in device-independent pixels for most geometry; you query per-window or per-screen devicePixelRatio() when you must draw in raw pixels (OpenGL, QImage/QPixmap). 
Qt ドキュメント

Qt unifies different OS reports (percentages, DPI, scale) into a device pixel ratio; it assumes base DPI (e.g., 96 on X11) when only DPI is known. 
Qt ドキュメント

Environment overrides (QT_SCALE_FACTOR, QT_SCREEN_SCALE_FACTORS, rounding policy) enable testing and compensating for platform quirks—good model for exposing override hooks in your add-on. 
Qt ドキュメント

1.3 macOS / Apple Platforms
Apple UI is expressed in points (user space units) which are mapped to device pixels by a scale factor (@1x, @2x/Retina, @3x). High-resolution (“HiDPI”) displays render 1 point as multiple pixels; OS X (macOS) treats points as floats to allow sub-pixel precision. 
Apple Developer
Apple Developer

Cocoa automatically scales most vector/path drawing with the current backing scale; you usually draw in points and let the system map to pixels. Explicit pixel work should query APIs like -[NSWindow backingScaleFactor]. 
Apple Developer
Apple Developer

1.4 GTK / GNOME / Linux Ecosystem
GTK historically supported integer scale factors (1, 2) for whole-UI scaling; fractional scaling for fonts came first; fractional whole-UI scaling is evolving (often compositor does upscale/downscale to approximate 1.25×, 1.5× etc.). 
Arch Wiki
wiki.gnome.org

API calls: gdk_monitor_get_scale_factor(), gtk_widget_get_scale_factor(), env vars GDK_SCALE & GDK_DPI_SCALE override behavior—mirrors need to detect actual vs forced scale. 
https://docs.gtk.org
https://docs.gtk.org

Real-world HiDPI configs (Arch, JetBrains notes) show composite scale = system × user override; expect non-integral effective factors. 
intellij-support.jetbrains.com
Arch Wiki

1.5 Blender (as a Host Environment)
Blender exposes View UI scale (context.preferences.view.ui_scale) that directly affects widget & font sizes. 
docs.blender.org

System scale helpers: context.preferences.system.ui_scale & ui_line_width provide additive info for custom drawing; values derive from OS DPI & Blender’s UI scale. 
docs.blender.org

For crisp text drawing, community guidance: compute DPI for BLF text as context.preferences.system.dpi * context.preferences.system.pixel_size (pixel density multiplier), then size fonts accordingly—illustrates how Blender multiplies OS DPI by pixel size to adapt to HiDPI. 
Blender Artists Community
docs.blender.org

2. Best Practices for Resolution-Independent UI Design
Design in logical units; rasterize at needed scale; re-layout on DPI change; avoid hard-coded pixel constants; snap hairlines to pixel grid; provide scalable assets. These recur across Windows PMv2 guidance, Qt High DPI doc, and Apple HiDPI guidelines. 
Microsoft Learn
Qt ドキュメント
Apple Developer

Use vector or multi-resolution images (@1x/@2x/@3x on Apple; scaled theme bitmaps on Windows PMv2; high-DPI pixmaps in Qt). 
Apple Developer
Microsoft Learn
Qt ドキュメント

Recompute cached metrics on DPI change (fonts, control sizes, icon bitmaps) or you’ll get mismatched UI after monitor moves—a specific gotcha flagged in Windows guidance and reflected in cross-platform dev community practice. 
Microsoft Learn
Qt ドキュメント
intellij-support.jetbrains.com

3. Common Scaling Factors & Rationale
Concept	Typical Base	Example Factors	Rationale
Windows logical inch	96 dpi base	100%, 125%, 150% etc.	Historical 96 mapping; user accessibility scaling. 
Microsoft Learn
Microsoft Learn
Apple points	1pt user space	@1x, @2x, @3x	Maintain apparent size across Retina densities. 
Apple Developer
Apple Developer
GTK scale	1 logical	2 integer; compositor fractional overlays	HiDPI support matured gradually; integer scaling core, fractional via compositor/env. 
Arch Wiki
wiki.gnome.org
Blender UI	User pref scale × system DPI × pixel_size	—	Combine OS DPI & user scaling for consistent UI in custom draws. 
Blender Artists Community
docs.blender.org
4. Floating-Point Precision & Scaled Coordinates
4.1 Why Exact Equality Fails
Even when two areas should share an edge, accumulated scaling & rounding mean their coordinates may differ by tiny deltas; naive == breaks adjacency detection. This is classic floating-point behavior: representation & rounding error, scale-dependent epsilons, and pitfalls near zero. 
Oracle Docs
Random ASCII - tech blog of Bruce Dawson
floating-point-gui.de

4.2 Robust Predicate Strategies
Adaptive precision predicates (Shewchuk) evaluate cheaply in float, fall back to extended precision if uncertainty remains—model for “filter then refine” gap tests. 
people.eecs.berkeley.edu

Error bounding & degeneracy registration (Wang et al., robust intersections) handle hierarchical tolerances before expensive tests—a pattern you can borrow: record “degenerate adjacency” first, then skip redundant higher-level checks. 
Computer Science and Engineering

ULP-based comparisons give scale-sensitive equality; relative vs absolute epsilon heuristics must treat near-zero specially. 
Random ASCII - tech blog of Bruce Dawson
floating-point-gui.de

5. Spatial Relationship Detection (Rectangles)
5.1 Axis-Aligned Rectangle Model
Represent each area as [x_min, x_max) × [y_min, y_max) in a normalized logical space (float). AABB structures (used broadly in graphics & physics) rely on min/max extents and are fast to test. 
Martin Cavarga
ウィキペディア

5.2 Overlap & Gap Primitives
Given A & B:

overlap_x = min(A.x_max, B.x_max) - max(A.x_min, B.x_min)
overlap_y = min(A.y_max, B.y_max) - max(A.y_min, B.y_min)

gap_x = max(0, max(A.x_min, B.x_min) - min(A.x_max, B.x_max))   # positive if separated horizontally
gap_y = max(0, max(A.y_min, B.y_min) - min(A.y_max, B.y_max))   # positive if separated vertically
Use signed deltas when you need direction; clamp >0 to get separations. These are the same primitives used in AABB collision culling & R-tree filtering. 
Martin Cavarga
ウィキペディア

5.3 Adjacency Test (Tolerance-Aware)
Two rects are adjacent horizontally if:

gap_x <= tol

overlap_y >= min_span (after expanding by tol)

They are not significantly overlapping (i.e., intersection area < tol_area) unless you accept “overlapping adjacency” class.

Similarly for vertical adjacency. These rule-sets mirror how spatial index nodes decide traversal vs prune under bounding boxes. 
ウィキペディア
Computer Science and Engineering
people.eecs.berkeley.edu

5.4 Tolerance Expansion / Shrink Wrapping
Before testing, you may expand each rect by ±tol/2 to absorb rounding error (Minkowski sum) then test exact integer comparisons; this mimics “layout rounding” and robust intersection staging. 
Microsoft Learn
Computer Science and Engineering
people.eecs.berkeley.edu

6. Robust Gap Detection Strategies
6.1 Multi-Tier Tolerance
Compute three tolerances:

Symbol	Meaning	Recommended Basis
tol_px	1 physical device pixel (minimum visible gap)	1 / scale_factor in logical units. 
Qt ドキュメント
Microsoft Learn
tol_ui	Blender UI granularity (user scale + pixel_size)	(system.dpi * pixel_size) / base_dpi derived; see BLF guidance. 
Blender Artists Community
docs.blender.org
tol_rel	Relative FP tolerance	`k * max(
Final tolerance: tol = max(tol_px, tol_ui, tol_rel); optionally clamp with user override slider (expose in add-on prefs). 
floating-point-gui.de
Microsoft Learn
docs.blender.org

6.2 Data-Driven Adaptive Tolerance
Scan all area edges; build histogram of unique coordinate values sorted; measure smallest non-zero delta; choose tolerance slightly above median of low quantile to absorb jitter but still detect real 1-px gaps—useful when unknown composite scales (GTK fractional, custom Blender UI scale) are in play. Pattern is analogous to R-tree bulk-loading heuristics that infer distribution to set node splits. 
ウィキペディア
intellij-support.jetbrains.com

6.3 Hierarchical Gap Classification
Borrowing from robust intersection staging: classify degenerate (|gap| ≤ tol), micro gap (tol < gap ≤ 2tol_px), visible gap (>2tol_px). This defers expensive redraw or re-layout only for visible gaps while merging degenerates into adjacency graph. 
Computer Science and Engineering
Microsoft Learn

6.4 Pixel-Grid Snapping Pass
Optional pass: snap all coords to nearest integer device pixel after scaling; record residual error; if residual > threshold, fall back to float tests. Mirrors Windows layout rounding; reduces cascade drift. 
Microsoft Learn
Microsoft Learn

7. Simplified Detection Algorithm (Pseudocode)
Below is a lean, dependency-light pipeline appropriate for a Blender add-on that must tolerate cross-platform scaling quirks.

# 1. Gather environment metrics (lazy cached; invalidate on DPI change or area resize)
env = {
    "bl_ui_scale": C.preferences.view.ui_scale,
    "bl_sys_ui_scale": C.preferences.system.ui_scale,
    "bl_sys_dpi": C.preferences.system.dpi,
    "bl_pixel_size": C.preferences.system.pixel_size,
    # optionally sample C.window.width/height -> monitor DPI heuristics
}

# 2. Normalize: choose working logical units = Blender "UI px"
base_dpi = 96.0  # use as normalization anchor only
env["logical_scale"] = env["bl_ui_scale"] * env["bl_sys_ui_scale"] * (env["bl_sys_dpi"] * env["bl_pixel_size"] / base_dpi)

def to_logical(x_px):
    return x_px / env["logical_scale"]

# 3. Build rect list in logical coords
rects = [Rect(to_logical(r.x), to_logical(r.y),
              to_logical(r.x + r.w), to_logical(r.y + r.h)) for r in collect_blender_areas()]

# 4. Compute adaptive tolerance
tol_px  = 1.0 / env["logical_scale"]
tol_ui  = max(1e-6, tol_px * 0.5)  # seed; refine below
deltas  = sorted(unique_edge_deltas(rects))
if deltas:
    quant = percentile(deltas, 5)
    tol_ui = max(tol_ui, quant * 0.5)
tol_rel = max_abs_coord(rects) * 4 * sys.float_info.epsilon  # 4 ULP guard

tol = max(tol_px, tol_ui, tol_rel)

# 5. Build adjacency
for i,a in enumerate(rects):
    for j,b in enumerate(rects[i+1:], i+1):
        if is_adjacent(a,b,tol):
            graph.add_edge(i,j)
        else:
            record_gap(a,b,measure_gap(a,b))

# 6. Optional R-tree acceleration if n large
Environment fields correspond to Blender API properties documented in PreferencesView/PreferencesSystem & BLF font sizing examples. 
docs.blender.org
docs.blender.org
Blender Artists Community

The “1px/baseDPI normalization” idea follows Windows DIP guidance (96 base) and Qt’s practice of normalizing from various OS reports; adapt the base to Blender conventions as needed. 
Microsoft Learn
Qt ドキュメント

8. Performance Considerations
Naïve O(n²) adjacency checks are fine for Blender-scale area counts (typically small), but if you ever generalize to hundreds/thousands of sub-rects (e.g., tiled layouts, overlay widgets), move to a spatial index (AABB tree or R-tree). These prune comparisons by bounding box tests & hierarchical grouping. 
ウィキペディア
Martin Cavarga

Bulk-loading / grouping by grid (grid bucketing keyed by quantized edge coordinates) is extremely fast and mirrors grid methods in “largest interior rectangle” & spatial index literature. 
evryway.com
ウィキペディア

Branching factor trade-offs in R-trees matter only at scale; defaults of 8–16 children produce good cache behavior (community spatial search discussions). 
Reddit
ウィキペディア

9. Edge Cases in Rectangle Adjacency
Edge Case	Symptom	Strategy
Sliver overlap (	overlap	< tol but > 0)
Micro gaps (	gap	≤ tol)
Floating-pt drift across rows/cols	Accumulated rounding yields gradually widening gaps	Snap to canonical grid; recompute from first column/row anchor. 
Microsoft Learn
Microsoft Learn
Mixed integer/fractional scale (GTK fractional fonts only)	Text & widgets misaligned; inconsistent edges	Use separate axis tolerances derived from measured edges in each region. 
Arch Wiki
wiki.gnome.org
Multi-monitor DPI change mid-session	Inconsistent cached scale values	Listen for DPI change notifications (Windows PMv2 model) & rebuild normalization. 
Microsoft Learn
Qt ドキュメント
10. Platform-Agnostic Scaling Principles (Actionable)
Principle A – Measure, don’t assume. Always query the active scale (per monitor) via host API, with user overrides. Windows PMv2 & Qt show why: monitors differ; users move windows. 
Microsoft Learn
Qt ドキュメント

Principle B – Normalize once. Convert everything into a single internal logical unit (e.g., Blender UI px) at the start of a layout pass; only convert back when drawing pixel-exact primitives. Apple points / Qt device-independent px illustrate the benefits. 
Apple Developer
Qt ドキュメント

Principle C – Re-layout on scale change. Hook signals/events analogous to WM_DPICHANGED, or poll Blender prefs on region redraw; cached metrics become invalid. 
Microsoft Learn
docs.blender.org

Principle D – Snap thin geometry. For 1-px lines, snap to pixel grid or use layout rounding to avoid blurring. 
Microsoft Learn
Microsoft Learn

Principle E – Provide multi-res assets. Use vector or multi-scale bitmaps; Apple @2x/@3x model is the canonical reference. 
Apple Developer
Microsoft Learn

11. Recommended Tolerance Calculation Strategies (Detail)
11.1 Compute Physical Pixel Size in Logical Units
tol_px = logical_units_per_device_pixel = 1 / (env.logical_scale_devices). This is your irreducible minimum—anything smaller is invisible anyway. Windows DIP mapping & Qt device pixel ratio illustrate this scaling. 
Microsoft Learn
Qt ドキュメント

11.2 Incorporate Blender UI Multiplier
tol_ui = tol_px * max(bl_ui_scale, bl_sys_ui_scale)—guards against user-upped UI scale thickening edges; Blender exposes both view & system ui_scale for this purpose. 
docs.blender.org
docs.blender.org

11.3 Scale by Pixel Density Multiplier
For text/draw handlers, compute dpi_eff = system.dpi * system.pixel_size; convert to logical relative to base (96) to handle HiDPI exactly as Blender community BLF guidance recommends. 
Blender Artists Community
docs.blender.org

11.4 Relative FP Guard
When coords get large (zoomed UI, large virtual space), relative epsilon scaled by max(|coord|) * machine_eps prevents missing adjacency due to representational growth—per FP comparison best practices. 
Random ASCII - tech blog of Bruce Dawson
Oracle Docs

11.5 Fractional-Scaling Safety (GTK)
Because GTK historically rounds to integer scale but fonts can scale fractionally, edges may land between pixel boundaries; inflate tolerance by small fraction (e.g., 0.25 px) when detected; guided by GTK HiDPI & GNOME HiDpi notes. 
Arch Wiki
wiki.gnome.org

12. Design Patterns for UI Framework Abstraction
12.1 Measurement Provider Interface
Define a narrow interface your detection code calls:

class UIScaleProbe:
    def logical_scale(self) -> float: ...
    def pixel_aspect(self) -> float: ...  # if non-square px ever matter
    def layout_rounding(self) -> bool: ...
Back each method with platform-specific queries (Blender, OS env) but keep the consumer agnostic. Pattern inspired by Qt’s cross-platform translation of OS scale modalities & Windows PMv2’s explicit declarations. 
Qt ドキュメント
Microsoft Learn

In Blender, the concrete probe reads from context.preferences.* as documented in PreferencesView/PreferencesSystem. 
docs.blender.org
docs.blender.org

12.2 Scale Change Notifier
Observer pattern: subscribe to DPI/scale change signals (where available) or poll at redraw; Windows PMv2’s WM_DPICHANGED & Qt’s QWindow::devicePixelRatioChanged pattern show why this is essential. 
Microsoft Learn
Qt ドキュメント

12.3 Resource Resolver
Given a logical size request for an icon, choose the nearest asset bucket (@1x/@2x/@3x) or vector fallback; Apple HIG images show multi-asset packaging; Windows PMv2 recommends reloading bitmaps per DPI. 
Apple Developer
Microsoft Learn

12.4 Pixel-Snap Adapter
Optional decorator that takes layout rects and applies pixel rounding when the host framework is known to do so (XAML layout rounding, GTK integer scaling). 
Microsoft Learn
https://docs.gtk.org

13. Mathematical Foundation for Robust Rectangle Adjacency Detection
Problem: Given set of axis-aligned rectangles 
R
i
=
[
x
i
0
,
x
i
1
)
×
[
y
i
0
,
y
i
1
)
R 
i
​
 =[x 
i
0
​
 ,x 
i
1
​
 )×[y 
i
0
​
 ,y 
i
1
​
 ) in 
R
2
R 
2
  subject to floating-point perturbations from scaling, decide if 
R
a
R 
a
​
  & 
R
b
R 
b
​
  are adjacent (share an edge) vs separated by gap 
g
>
0
g>0 vs overlapping.

Core invariants:

Sort edges; adjacency implies one interval endpoint aligns (within tol) to another’s start in one axis, while intervals overlap (≥ min_span) on the orthogonal axis.

Represent comparisons with interval arithmetic + tolerance expansion: expand each interval: 
[
x
0
−
δ
,
x
1
+
δ
]
[x 
0
 −δ,x 
1
 +δ]. If expanded intervals overlap but original do not, classify as adjacency within tolerance. This follows robust predicate “filter then widen” pattern. 
people.eecs.berkeley.edu
Computer Science and Engineering

When grid is intended to tile without gaps, you can enforce global conservation: sum of widths per row = container width within tolerance; use this to distribute residual error (layout rounding concept). 
Microsoft Learn
Microsoft Learn

Use hierarchical grouping (BVH / R-tree) when N large; adjacency edges only considered among rects whose expanded AABBs touch. 
ウィキペディア
Martin Cavarga

14. Putting It Together for Blender
14.1 Gather Blender Metrics Reliably
C.preferences.view.ui_scale (user-visible UI scale slider). 
docs.blender.org

C.preferences.system.ui_scale, ui_line_width, dpi, pixel_size (system metrics & suggestions for add-ons). 
docs.blender.org

BLF text sizing best practice: dpi = system.dpi * system.pixel_size—useful template for deriving composite scale. 
Blender Artists Community

14.2 Normalize Areas
Convert region pixel coordinates to logical UI units using composite scale above; keep double precision floats to minimize loss; only snap at end if needed. Blender’s own mixed use of UI vs pixel metrics in draw handlers motivates centralizing this conversion. 
Blender Artists Community
docs.blender.org

14.3 Dynamic Recalc
If user changes Blender UI scale in Preferences or moves Blender between monitors with different OS DPI (common Windows PMv2 scenario), recompute environment scale before the next adjacency pass. 
Microsoft Learn
docs.blender.org

15. Best Practices for Minimizing Hard-Coded Dependencies
Query, cache, invalidate — never bake 96, 2×, etc.; read from Blender prefs & OS signals. (Windows & Qt both warn against assuming single DPI.) 
Microsoft Learn
Qt ドキュメント

Expose override knob for user to nudge tolerance when running in exotic desktop environments (GTK fractional, remote desktop scaling). 
Arch Wiki
intellij-support.jetbrains.com

Prefer relative math (differences between measured edges) over absolute pixel constants; Apple & Qt both rely on points/device-independent px precisely to avoid pixel constants. 
Apple Developer
Qt ドキュメント

Snap only at final render; keep float internally; XAML layout rounding shows rounding is a presentation concern. 
Microsoft Learn

Multi-res assets; load based on measured scale; Apple @2x model & Windows PMv2 bitmap reload guidance. 
Apple Developer
Microsoft Learn

16. Focus Question Answers
Q1. Theoretical minimum information needed to detect rectangle adjacency?
At minimum (assuming axis alignment): each rectangle’s min & max extents in X and Y in a common coordinate space. With those four numbers per rect you can derive overlaps and gaps; no need for area IDs or ordering. A global tolerance scalar (or per-axis) is required when coordinates are floating-point. Bounding volume methods (AABB, R-tree) operate entirely on these extents, demonstrating sufficiency. 
Martin Cavarga
ウィキペディア

Q2. How do successful cross-platform apps handle UI scaling variations?
They (1) adopt a logical coordinate system (points/DIPs), (2) query per-monitor scale changes at runtime, (3) re-layout & re-rasterize assets when scale changes, (4) provide multi-resolution resources, and (5) optional pixel-grid snap for crisp lines. This pattern is explicit in Windows PMv2 docs, Qt High DPI, and Apple HiDPI guidelines. 
Microsoft Learn
Qt ドキュメント
Apple Developer

Q3. Most robust mathematical approaches for coordinate precision issues?
Use a layered strategy: fast float tests + tolerance expansion; escalate to higher-precision or symbolic predicates when uncertainty remains (Shewchuk adaptive predicates). Combine absolute & relative epsilons (ULPs) and handle near-zero values specially (FP comparison best practices). Register degeneracies early to short-circuit cascading error (robust intersection staging). 
people.eecs.berkeley.edu
Random ASCII - tech blog of Bruce Dawson
Computer Science and Engineering

Q4. Design a system that adapts to unknown scaling factors automatically?
Measure runtime scale from host (Blender prefs + OS/monitor metrics); if missing/ambiguous, infer from observed widget geometry (edge deltas histogram). Apply fallback environment variables (like Qt & GTK do) to override; recalc on resize/DPI change events. Use derived composite scale for normalization; expose user override. 
Qt ドキュメント
wiki.gnome.org
docs.blender.org

17. Next Steps (If You’d Like)
If you want, I can help you:

Write a small Blender utility that prints the current composite UI scale & recommended tolerance.

Build a test harness that perturbs area rectangles by random sub-pixel noise and verifies adjacency classification stability.

Integrate a minimal R-tree or grid bucket accelerator (pure Python, no external deps) for larger layouts.

Let me know which of these you’d like to tackle first.


