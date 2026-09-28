"""VoR-QFD-Taguchi-GD&T toolkit.

Companion implementation for "From Voice of Regulation to Robust Design
Utilizing QFD and Taguchi Methods to Translate P&ID Requirements into GD&T
Schemes for Process Equipment" (ICCBI-2026).

Modules follow the four phases of the paper's Figure 1:

* :mod:`vor_gdt.vor` - Phase 1, Voice of Regulation extraction (Eq. 1)
* :mod:`vor_gdt.hoq` - Phase 2, House of Quality prioritization (Eq. 2)
* :mod:`vor_gdt.taguchi`, :mod:`vor_gdt.orthogonal_arrays`,
  :mod:`vor_gdt.robust_design` - Phase 3, Taguchi robust design (Eq. 3)
* :mod:`vor_gdt.gdt`, :mod:`vor_gdt.traceability` - Phase 4, GD&T scheme
  formulation and traceability mapping

:mod:`vor_gdt.published` records the paper's Tables 1-3, kept
separate from the demonstration pipeline.
"""

__version__ = "1.0.0"
