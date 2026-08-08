# 🎨 SilkTrace CSS Snippets & Styling Reference

## Quick Copy-Paste Solutions

---

## 🌈 COLOR PALETTE

### Professional Blue Theme (Current)
```python
# Primary colors
PRIMARY_BLUE = "#1f3a93"
DARK_BLUE = "#2d5aa6"
LIGHT_BLUE = "#e0e7ff"

# Status colors
SUCCESS_GREEN = "#22c55e"
WARNING_YELLOW = "#f59e0b"
ERROR_RED = "#ef4444"
INFO_CYAN = "#0ea5e9"

# Neutrals
WHITE = "#ffffff"
LIGHT_GRAY = "#f5f7fa"
MEDIUM_GRAY = "#64748b"
DARK_GRAY = "#1f2937"
```

### Copy-Paste Gradient CSS

```css
/* Blue Gradient */
background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);

/* Green Gradient */
background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);

/* Yellow Gradient */
background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);

/* Purple Gradient */
background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);

/* Red Gradient */
background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);

/* Dark Gradient */
background: linear-gradient(180deg, #1f3a93 0%, #2d5aa6 100%);
```

---

## 📦 COMPONENT SNIPPETS

### Professional Card/Box

```python
st.markdown("""
<div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 24px;
            border-radius: 12px;
            border-left: 4px solid #0ea5e9;
            box-shadow: 0 2px 8px rgba(31, 58, 147, 0.08);">
<h4 style="color: #0284c7; margin-top: 0;">🎯 Card Title</h4>
<p style="color: #0c4a6e;">Your content goes here</p>
</div>
""", unsafe_allow_html=True)
```

### Three-Column Gradient Cards

```python
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                padding: 24px;
                border-radius: 12px;
                border-left: 4px solid #22c55e;">
    <h4 style="color: #16a34a;">Card 1</h4>
    <p>Content</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                padding: 24px;
                border-radius: 12px;
                border-left: 4px solid #f59e0b;">
    <h4 style="color: #d97706;">Card 2</h4>
    <p>Content</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                padding: 24px;
                border-radius: 12px;
                border-left: 4px solid #0ea5e9;">
    <h4 style="color: #0284c7;">Card 3</h4>
    <p>Content</p>
    </div>
    """, unsafe_allow_html=True)
```

### Status Indicator Card

```python
# High Confidence
st.markdown("""
<div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #22c55e;
            text-align: center;">
<h3 style="color: #16a34a; margin: 0;">✅ High Confidence</h3>
<p style="color: #15803d;">Detection is reliable</p>
</div>
""", unsafe_allow_html=True)

# Moderate Confidence
st.markdown("""
<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #f59e0b;
            text-align: center;">
<h3 style="color: #d97706; margin: 0;">ℹ️ Moderate Confidence</h3>
<p style="color: #92400e;">Manual review recommended</p>
</div>
""", unsafe_allow_html=True)

# Low Confidence
st.markdown("""
<div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #ef4444;
            text-align: center;">
<h3 style="color: #dc2626; margin: 0;">❌ Low Confidence</h3>
<p style="color: #991b1b;">Inspection required</p>
</div>
""", unsafe_allow_html=True)
```

### Alert Message Box

```python
# Success Alert
st.markdown("""
<div style="background-color: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 15px;
            border-radius: 8px;">
<strong style="color: #16a34a;">✅ Success:</strong>
<span style="color: #15803d;"> Your operation was successful!</span>
</div>
""", unsafe_allow_html=True)

# Info Alert
st.markdown("""
<div style="background-color: #f0f9ff;
            border-left: 4px solid #0ea5e9;
            padding: 15px;
            border-radius: 8px;">
<strong style="color: #0284c7;">ℹ️ Information:</strong>
<span style="color: #0c4a6e;"> Here's something you should know.</span>
</div>
""", unsafe_allow_html=True)

# Warning Alert
st.markdown("""
<div style="background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            border-radius: 8px;">
<strong style="color: #d97706;">⚠️ Warning:</strong>
<span style="color: #92400e;"> Please review this warning.</span>
</div>
""", unsafe_allow_html=True)

# Error Alert
st.markdown("""
<div style="background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            border-radius: 8px;">
<strong style="color: #dc2626;">❌ Error:</strong>
<span style="color: #991b1b;"> An error has occurred.</span>
</div>
""", unsafe_allow_html=True)
```

### Result Display Card

```python
# For prediction results
st.markdown("""
<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #f59e0b;">
<h3 style="color: #d97706; margin: 0;">⚡ Energy Prediction</h3>
<p style="font-size: 2.5rem; font-weight: bold; color: #b45309; margin: 10px 0;">
45.23 kWh
</p>
<p style="color: #92400e; margin: 0;">Predicted Energy Usage</p>
</div>
""", unsafe_allow_html=True)
```

---

## 📊 CHART STYLING

### Professional Plotly Chart

```python
import plotly.express as px
import plotly.graph_objects as go

# Bar chart with professional styling
fig = px.bar(
    data_frame,
    x="column_x",
    y="column_y",
    title="Chart Title",
    color_discrete_sequence=["#0ea5e9"]
)

fig.update_layout(
    height=400,
    plot_bgcolor="rgba(240,249,255,0.5)",
    paper_bgcolor="white",
    showlegend=False,
    hovermode="x unified",
    xaxis_title="X Axis",
    yaxis_title="Y Axis"
)

st.plotly_chart(fig, use_container_width=True)
```

### Color Schemes for Charts

```python
# Professional color palettes
BLUE_PALETTE = ["#0ea5e9", "#0284c7", "#0c4a6e"]
GREEN_PALETTE = ["#22c55e", "#16a34a", "#15803d"]
WARM_PALETTE = ["#ef4444", "#f59e0b", "#0ea5e9"]
PROFESSIONAL = ["#1f3a93", "#2d5aa6", "#0ea5e9"]

# Use in charts
fig = px.bar(
    df,
    color_discrete_sequence=PROFESSIONAL
)
```

---

## 🎯 BUTTON STYLING

### Large Call-to-Action Button

```python
if st.button("🚀 Predict Energy Usage", use_container_width=True):
    # Your logic here
    pass
```

### Multiple Buttons in Row

```python
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Download PDF", use_container_width=True):
        pass

with col2:
    if st.button("📊 Download CSV", use_container_width=True):
        pass
```

### Styled Download Buttons

```python
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📄 PDF Report",
        data=pdf_data,
        file_name="report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with col2:
    st.download_button(
        label="📊 CSV Export",
        data=csv_data,
        file_name="data.csv",
        mime="text/csv",
        use_container_width=True
    )
```

---

## 📱 TEXT & TYPOGRAPHY

### Large Title with Color

```python
st.markdown("""
<h1 style="color: #1f3a93; text-align: center; font-size: 3rem;">
🧵 SilkTrace
</h1>
""", unsafe_allow_html=True)
```

### Subtitle with Tagline

```python
st.markdown("""
<h3 style="color: #64748b; text-align: center; font-style: italic;">
AI-Powered Textile Intelligence System
</h3>
""", unsafe_allow_html=True)
```

### Section Header with Icon

```python
st.markdown("""
<h2 style="color: #1f3a93; border-bottom: 3px solid #e0e7ff; padding-bottom: 10px;">
📊 Analytics Dashboard
</h2>
""", unsafe_allow_html=True)
```

### Professional Caption

```python
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 2rem;">
<p><strong>SilkTrace</strong> | AI-Powered Smart Textile System</p>
<p>© 2024 | Developed by Your Name</p>
</div>
""", unsafe_allow_html=True)
```

---

## 🌓 THEME VARIATIONS

### Dark Professional Theme

```python
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

h1, h2, h3 {
    color: #ffffff;
}

[data-testid="metric-container"] {
    background-color: #0f3460;
    border: 2px solid #533483;
    color: #ffffff;
}

.stButton > button {
    background: linear-gradient(135deg, #e94560 0%, #f77f00 100%);
}
</style>
""", unsafe_allow_html=True)
```

### Minimalist Gray Theme

```python
st.markdown("""
<style>
.main {
    background: #f9fafb;
}

h1, h2, h3 {
    color: #374151;
}

[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
}

.stButton > button {
    background: #6b7280;
}
</style>
""", unsafe_allow_html=True)
```

### Vibrant Modern Theme

```python
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
}

h1, h2, h3 {
    color: #7c3aed;
}

[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 2px solid #c4b5fd;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%);
}
</style>
""", unsafe_allow_html=True)
```

---

## 🔧 LAYOUT COMPONENTS

### Three-Column Section Header

```python
st.markdown("### 📊 Section Title")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Metric 1", "100")

with col2:
    st.metric("Metric 2", "200")

with col3:
    st.metric("Metric 3", "300")
```

### Two-Column Content Layout

```python
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Large Content")
    # Your main content
    pass

with col2:
    st.markdown("### Sidebar")
    # Your sidebar content
    pass
```

### Sidebar Component

```python
with st.sidebar:
    st.markdown("## System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Status", "Online", "✅")
    
    with col2:
        st.metric("Models", "3", "Ready")
```

---

## 📐 SPACING & PADDING

### Add Dividers

```python
# Line divider
st.divider()

# Markdown divider with custom style
st.markdown("""
<div style="border: none; height: 2px; 
background: linear-gradient(90deg, #e0e7ff 0%, #c7d2fe 50%, #e0e7ff 100%);
margin: 2rem 0;"></div>
""", unsafe_allow_html=True)
```

### Add Vertical Space

```python
# Small space
st.markdown("")

# Medium space
st.markdown("")
st.markdown("")

# Custom space
st.markdown("""
<div style="margin: 2rem 0;"></div>
""", unsafe_allow_html=True)
```

### Add Horizontal Space

```python
col1, col2, col3 = st.columns([1, 8, 1])
with col2:
    # Content centered with space on sides
    pass
```

---

## 🎭 EXPANDER STYLING

### Professional Expander

```python
with st.expander("ℹ️ Model Information"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Model:** MobileNetV2")
        st.markdown("**Framework:** TensorFlow")
    
    with col2:
        st.markdown("**Classes:** 3")
        st.markdown("**Input Size:** 224×224")
```

---

## 📋 TABLE STYLING

### Professional Dataframe Display

```python
# Basic
st.dataframe(df, use_container_width=True, hide_index=True)

# With selection
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Column1": st.column_config.NumberColumn("Label", format="$ %d"),
    }
)
```

### Custom HTML Table

```python
table_html = """
<table style="width: 100%; border-collapse: collapse;">
<tr style="background-color: #1f3a93; color: white;">
<th style="padding: 10px; text-align: left;">Column 1</th>
<th style="padding: 10px; text-align: left;">Column 2</th>
</tr>
<tr>
<td style="padding: 10px; border-bottom: 1px solid #e0e7ff;">Data 1</td>
<td style="padding: 10px; border-bottom: 1px solid #e0e7ff;">Data 2</td>
</tr>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)
```

---

## 🎨 COMMON PATTERNS

### Info Box Pattern

```python
st.info("💡 **Helpful Tip:** Your tip text here")
```

### Success Pattern

```python
st.success("✅ **Success:** Your success message here")
```

### Warning Pattern

```python
st.warning("⚠️ **Warning:** Your warning message here")
```

### Error Pattern

```python
st.error("❌ **Error:** Your error message here")
```

---

## 🚀 Copy-Paste Ready Sections

### Professional Header

```python
st.markdown("## 📊 Your Page Title")
st.markdown("*Your subtitle or description*")
st.markdown("---")
```

### KPI Section

```python
st.markdown("### 📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Metric 1", "100")

with col2:
    st.metric("Metric 2", "200")

with col3:
    st.metric("Metric 3", "300")

with col4:
    st.metric("Metric 4", "400")

st.markdown("---")
```

### Chart Section

```python
st.markdown("### 📈 Chart Title")

col1, col2 = st.columns(2)

with col1:
    # Chart 1
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Chart 2
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
```

### Footer Section

```python
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem;">
<p><strong>App Name</strong> | Your subtitle</p>
<p>© 2024 | Your Organization</p>
</div>
""", unsafe_allow_html=True)
```

---

## 🎓 Tips & Tricks

1. **Always use `use_container_width=True`** for charts and buttons to maximize space
2. **Organize inputs into columns** to reduce scrolling
3. **Use dividers (`st.divider()`)** to separate sections
4. **Color-code elements** for quick visual recognition
5. **Add icons/emojis** for better UX
6. **Use gradients** for premium appearance
7. **Implement hover effects** for interactivity
8. **Keep consistent spacing** throughout the app
9. **Use professional fonts** - avoid excessive styling
10. **Test on mobile** - ensure responsive design

---

**Happy Styling! 🎨**
