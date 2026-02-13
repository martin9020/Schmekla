# Project: 704216 - Domino Printing Loading Bay Canopy

## Quick Reference
| Field | Value |
|-------|-------|
| Job Number | 704216 |
| Client | Domino Printing |
| Location | L30 4AJ |
| Product | Oxford XL |
| Contractor | Clovis Canopies |
| Drawn By | GMC |

## Structure Specifications

### Overall Dimensions
- Length: 13,000mm (X-direction)
- Width: 10,000mm (Y-direction)
- Eaves Height: 4,865mm
- Ridge Height: 6,980mm
- Roof Type: Barrel (curved)
- Cladding: Polycarbonate

### Grid System
**X-Direction (numbered grids):**
| Grid | Position |
|------|----------|
| 1 | 0mm |
| 2 | 2,500mm |
| 3 | 5,000mm |
| 4 | 7,500mm |
| 5 | 10,000mm |

**Y-Direction (lettered grids):**
| Grid | Position |
|------|----------|
| B | 0mm |
| C | 10,000mm |

### Structural Elements

#### Columns (10 total)
- Profile: SHS 150x150x5
- Height: 5,716mm
- Locations: All grid intersections (B1, B2, B3, B4, B5, C1, C2, C3, C4, C5)
- Marks: COL1 (corners at 1,5), COL6 (intermediate at 2,3,4)

#### Barrel Hoops (5 hoops, 80 segments total)
- Profile: SHS 60x60x4
- Span: 10,000mm (B to C)
- Segments per hoop: 16
- Rise: 2,115mm (parabolic curve)
- Locations: One hoop at each X-grid (1, 2, 3, 4, 5)

#### Purlins (68 total)
- Standard: SHS 60x60x3 (PURL6) - 56 pieces
- Edge: SHS 60x60x4 (PURL10) - 12 pieces
- Length: ~2,500mm (between grid lines)
- Spacing: 17 positions along each hoop

#### Foundations (10 pads)
- Corner pads (grids 1 & 5): 1,200 x 1,200 x 300mm
- Intermediate pads (grids 2, 3, 4): 1,400 x 1,400 x 300mm
- Material: Concrete C30/37

## Model Statistics
- Total elements: 168
- Footings: 10
- Columns: 10
- Beam segments: 148 (hoops + purlins)

## Files Generated
| File | Description |
|------|-------------|
| `model.schmekla` | Native Schmekla model |
| `704216_Domino_Printing_Canopy.ifc` | IFC2X3 export (Tekla compatible) |

## Source Documents
Located in `Conditions/`:
- `704216-2-Domino Printing-Provisional GA.pdf` - Main GA drawing
- `704216-3-Domino Printing-GA - Columns - For inst.pdf`
- `704216-3-Domino Printing-GA - Hoops - For inst.pdf`
- `704216-3-Domino Printing-GA - Purlins - For inst.pdf`
- `704216-3-Domino Printing-Foundation GA.pdf`

## Technical Decisions

### Barrel Curve Approximation
Used parabolic curve with 16 segments:
```
z = z_eaves + 4 * rise * t * (1 - t)
```
Where t = 0 to 1 across the span.

### IFC Export Settings
- Schema: IFC2X3 (required for Tekla)
- Units: Millimeters
- Materials: S355 steel, C30/37 concrete

---
*Generated: 2026-01-25*
