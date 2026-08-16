---
name: Afiyati Healthcare System
colors:
  surface: '#101415'
  surface-dim: '#101415'
  surface-bright: '#353a3b'
  surface-container-lowest: '#0a0f10'
  surface-container-low: '#181c1d'
  surface-container: '#1c2021'
  surface-container-high: '#262b2c'
  surface-container-highest: '#313636'
  on-surface: '#dfe3e4'
  on-surface-variant: '#bdc9ca'
  inverse-surface: '#dfe3e4'
  inverse-on-surface: '#2d3132'
  outline: '#889395'
  outline-variant: '#3e494a'
  surface-tint: '#79d4e2'
  primary: '#79d4e2'
  on-primary: '#00363d'
  primary-container: '#087f8c'
  on-primary-container: '#effdff'
  inverse-primary: '#006874'
  secondary: '#69d8d1'
  on-secondary: '#003735'
  secondary-container: '#25a19b'
  on-secondary-container: '#00302e'
  tertiary: '#f1bc96'
  on-tertiary: '#49280e'
  tertiary-container: '#956a4a'
  on-tertiary-container: '#fff9f7'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#95f1ff'
  primary-fixed-dim: '#79d4e2'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f57'
  secondary-fixed: '#87f4ee'
  secondary-fixed-dim: '#69d8d1'
  on-secondary-fixed: '#00201e'
  on-secondary-fixed-variant: '#00504d'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#f1bc96'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#633e22'
  background: '#101415'
  on-background: '#dfe3e4'
  surface-variant: '#313636'
typography:
  headline-xl:
    fontFamily: Be Vietnam Pro
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 52px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Be Vietnam Pro
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 42px
  headline-md:
    fontFamily: Be Vietnam Pro
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Be Vietnam Pro
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  caption:
    fontFamily: Be Vietnam Pro
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 64px
  gutter: 20px
  margin-mobile: 20px
  margin-desktop: 80px
---

## Brand & Style

The design system is rooted in the philosophy of "Human-Centric Wellness." It balances clinical authority with a welcoming, accessible atmosphere, moving away from sterile "hospital" aesthetics toward a more holistic, premium healthcare experience. 

The visual style is **Modern Professional with Soft-Humanist touches**, now optimized for a high-performance **Dark Mode** environment. It utilizes depth through tonal layering rather than just whitespace, ensuring high-quality photography of real human interactions stands out against the deep UI. The interface is optimized for Right-to-Left (RTL) layouts as a primary consideration, ensuring the flow of information feels natural for Arabic speakers while maintaining a clean, systematic structure for bilingual support.

## Colors

This color palette is designed to evoke trust, vitality, and calm within a sophisticated dark interface.

- **Primary (Deep Medical Teal):** Used for primary brand elements, key CTAs, and structural headers. It provides the "anchor" of professional authority.
- **Secondary (Fresh Healthcare Green):** Used for accents, secondary actions, and health-tracking visuals. It adds a layer of freshness and growth.
- **Tertiary (Warm Earth/Sand):** A new addition used for specialized highlights, holistic wellness categories, or earthy accents that balance the cool teals.
- **Neutral System:** Optimized for dark mode. Backgrounds use deep, desaturated teals to reduce eye strain and maintain brand DNA, while surfaces use slightly lighter tones to create hierarchy.
- **Semantic Colors:** Emergency Red is reserved strictly for urgent health alerts; Success Green for completed appointments; Warning Orange for preventative advice.

## Typography

The design system uses **Be Vietnam Pro** for its contemporary, friendly, and highly legible characteristics. When implemented for Arabic, it should be paired with a high-quality typeface like **Tajawal** to maintain a consistent visual weight and x-height.

- **Hierarchical Contrast:** Use SemiBold (600) and Bold (700) weights for headlines to create clear entry points for information. 
- **Readability:** Body text should maintain a generous line height (minimum 1.5x font size) to ensure accessibility for users who may be viewing the app under physical or mental stress. In dark mode, font weights are carefully balanced to prevent "haloing" against dark backgrounds.
- **RTL Alignment:** All text is right-aligned by default. Numeric values in health reports should use localized numerals where appropriate but maintain clear, tabular spacing.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a focus on generous white space (or "dark space") to prevent "cognitive overload," which is critical in healthcare settings.

- **Grid System:** Use a 12-column grid for desktop and a 4-column grid for mobile.
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **RTL Considerations:** Layout directions, chevron icons, and progress bars must be mirrored. The "leading" edge is the right side.
- **Density:** Maintain a low-to-medium density. Information is chunked into logical sections using cards and wide gutters (20px) to ensure no single screen feels cluttered.

## Elevation & Depth

This design system uses **Tonal Layers** and **Subtle Inner Glows** to create hierarchy in its dark theme, ensuring interactive surfaces are easily distinguishable.

- **Level 0 (Background):** The lowest layer, a deep neutral-teal base.
- **Level 1 (Cards/Surfaces):** Slightly lighter surfaces with a soft, diffused shadow to indicate elevation.
- **Level 2 (Modals/Overlays):** The brightest surface tier to indicate temporary focus, often accompanied by a dimming backdrop layer.
- **Depth Cues:** In dark mode, elevation is primarily communicated by surface brightness—higher elements are lighter. Shadows are used sparingly with higher spread and lower opacity.

## Shapes

The shape language is defined by **Soft Roundedness**. This choice is intentional to avoid the "sharpness" associated with surgical instruments or clinical environments, instead conveying comfort and safety.

- **Standard Components:** Buttons and input fields use a 8px (rounded-md) radius.
- **Containers:** Main cards and content areas use a 24px (rounded-xl) radius.
- **Special Elements:** Avatars of medical professionals should be circular, while health "chips" or tags are pill-shaped for high contrast against rectangular content.

## Components

- **Buttons:** Primary buttons are solid Deep Medical Teal (#087F8C) with white text. Secondary buttons use a Fresh Healthcare Green (#3AAFA9) outline.
- **Input Fields:** Use a subtle border that thickens and changes to Primary Teal on focus. In dark mode, the input surface is slightly lighter than the main background for visibility.
- **Cards:** Layered surfaces with 24px radius. Cards should have a "Medical Header" style where a small icon or category chip is placed at the top right (RTL).
- **Chips/Status:** Use the Tertiary color (#B28361) for lifestyle or wellness tags. Status chips use low-opacity semantic colors with high-opacity text.
- **Progress Indicators:** Soft, rounded 8px bars. Use Primary or Secondary colors for positive progress and Tertiary for neutral health metrics.
- **Navigation:** A clean bottom-navigation bar on mobile with active states indicated by a Primary Teal icon and a small dot indicator below it.