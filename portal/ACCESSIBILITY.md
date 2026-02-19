# Accessibility Guide - RobCo Forge Portal

## Overview
The RobCo Forge Portal is designed to be accessible to all users, including those using assistive technologies.

## Keyboard Navigation

### Global Shortcuts
- `Ctrl/Cmd + D` - Navigate to Dashboard
- `Ctrl/Cmd + W` - Navigate to Workspaces
- `Ctrl/Cmd + B` - Navigate to Blueprints
- `Ctrl/Cmd + C` - Navigate to Costs
- `Ctrl/Cmd + L` - Navigate to Lucy AI
- `Ctrl/Cmd + ,` - Navigate to Settings
- `Ctrl/Cmd + /` - Focus search/chat
- `Escape` - Close modals and dialogs
- `Tab` - Navigate forward through interactive elements
- `Shift + Tab` - Navigate backward through interactive elements

### Skip Links
- "Skip to main content" link appears at the top of each page when focused

## Screen Reader Support

### ARIA Labels
All interactive elements include appropriate ARIA labels:
- Buttons have descriptive `aria-label` attributes
- Form inputs have associated labels
- Status messages use `aria-live` regions
- Modal dialogs use `role="dialog"` and `aria-modal="true"`

### Semantic HTML
- Proper heading hierarchy (h1 → h2 → h3)
- Semantic elements (`<nav>`, `<main>`, `<aside>`, `<article>`)
- Form elements properly labeled
- Tables include `<thead>`, `<tbody>`, and proper scope attributes

### Live Regions
- Status updates announced via `aria-live="polite"`
- Critical alerts use `aria-live="assertive"`
- Loading states communicated to screen readers

## Visual Accessibility

### Focus Indicators
- All interactive elements have visible focus indicators
- Focus indicators are 3px solid outlines with 2px offset
- Modern theme: Blue (#3b82f6) focus indicators
- Retro theme: Green (#33ff33) focus indicators with glow effect

### Color Contrast
- Modern theme meets WCAG 2.1 AA standards (4.5:1 for normal text)
- Retro theme uses high-contrast green on black
- Status indicators use multiple visual cues (color + icon + text)

### Text Sizing
- Base font size: 16px
- Relative units (rem/em) used throughout
- Text remains readable when zoomed to 200%

## Reduced Motion

### Prefers Reduced Motion
The portal respects the `prefers-reduced-motion` media query:
- Animations disabled or reduced to minimal duration
- Scanline effects disabled in retro theme
- Transitions reduced to instant or very short
- Cursor blink animation disabled

### Manual Control
Users can disable animations via Settings:
- Theme selection affects animation intensity
- Retro theme animations can be disabled

## Form Accessibility

### Labels and Instructions
- All form fields have visible labels
- Required fields marked with asterisk and `aria-required`
- Error messages associated with fields via `aria-describedby`
- Placeholder text used as hints, not labels

### Error Handling
- Errors announced to screen readers
- Error messages appear near the relevant field
- Form validation provides clear, actionable feedback

## Modal Dialogs

### Focus Management
- Focus trapped within modal when open
- Focus returns to trigger element when closed
- First focusable element receives focus on open

### Keyboard Support
- `Escape` key closes modal
- `Tab` cycles through modal elements
- Close button always keyboard accessible

## Tables

### Data Tables
- Column headers use `<th>` with `scope="col"`
- Row headers use `<th>` with `scope="row"` where applicable
- Complex tables include `<caption>` for context
- Sortable columns indicate sort direction

## Images and Icons

### Alternative Text
- Decorative icons hidden from screen readers (`aria-hidden="true"`)
- Informative icons include text alternatives
- Emoji used sparingly and with text fallbacks

### Icon-Only Buttons
- Include `aria-label` for context
- Tooltip text matches aria-label

## Testing

### Automated Testing
- Run `npm run test:a11y` for automated accessibility checks
- Lighthouse accessibility audits in CI/CD

### Manual Testing
- Keyboard-only navigation testing
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Color contrast verification
- Zoom testing (up to 200%)

## Browser Support

### Assistive Technology Compatibility
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS, iOS)
- TalkBack (Android)
- ChromeVox (Chrome OS)

### Browser Requirements
- Modern browsers with ES6+ support
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## Reporting Issues

If you encounter accessibility issues:
1. Document the issue with steps to reproduce
2. Include browser and assistive technology details
3. Report via GitHub issues or internal ticketing system

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/resources/)
