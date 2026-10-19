import os
with open('requirements.txt', 'w') as f:
    f.write('streamlit>=1.30.0\npandas>=2.0.0\nplotly>=5.18.0\n')

app_code = """
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PharmaCare - Smart Pharmacy POS",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if "products" not in st.session_state:
    st.session_state.products = [
        {
            "id": "P001",
            "name": "Amoxicillin 500mg",
            "category": "Antibiotics",
            "price": 18.50,
            "stock": 45,
            "min_threshold": 10,
            "rx_required": True,
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=400&q=80"
        },
        {
            "id": "P002",
            "name": "Paracetamol Extra 650mg",
            "category": "Pain Relief",
            "price": 8.25,
            "stock": 4,  # Triggers low stock alert
            "min_threshold": 15,
            "rx_required": False,
            "image": "https://images.unsplash.com/photo-1550572017-edf706256363?auto=format&fit=crop&w=400&q=80"
        },
        {
            "id": "P003",
            "name": "Vitamin C 1000mg Effervescent",
            "category": "Vitamins",
            "price": 12.00,
            "stock": 30,
            "min_threshold": 8,
            "rx_required": False,
            "image": "https://images.unsplash.com/photo-1577401239170-897942555fb3?auto=format&fit=crop&w=400&q=80"
        },
        {
            "id": "P004",
            "name": "Emergency First Aid Kit",
            "category": "First Aid",
            "price": 34.99,
            "stock": 3,  # Triggers low stock alert
            "min_threshold": 5,
            "rx_required": False,
            "image": "https://images.unsplash.com/photo-1603398938378-e54eab446dde?auto=format&fit=crop&w=400&q=80"
        },
        {
            "id": "P005",
            "name": "Ibuprofen Softgels 400mg",
            "category": "Pain Relief",
            "price": 9.75,
            "stock": 60,
            "min_threshold": 12,
            "rx_required": False,
            "image": "https://images.unsplash.com/photo-1585435557343-3b092031a831?auto=format&fit=crop&w=400&q=80"
        }
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "sales_history" not in st.session_state:
    st.session_state.sales_history = []

# --- HELPER FUNCTIONS ---
def get_low_stock_items():
    return [p for p in st.session_state.products if p["stock"] <= p["min_threshold"]]

def add_to_cart(product_id):
    prod = next((p for p in st.session_state.products if p["id"] == product_id), None)
    if not prod or prod["stock"] <= 0:
        return
    
    cart_item = next((item for item in st.session_state.cart if item["id"] == product_id), None)
    if cart_item:
        if cart_item["qty"] < prod["stock"]:
            cart_item["qty"] += 1
        else:
            st.toast(f"⚠️ Maximum available stock ({prod['stock']}) reached for {prod['name']}", icon="⚠️")
    else:
        st.session_state.cart.append({
            "id": prod["id"],
            "name": prod["name"],
            "price": prod["price"],
            "qty": 1
        })
    st.toast(f"Added {prod['name']} to cart", icon="🛒")

def process_checkout(customer_name):
    if not st.session_state.cart:
        return None
    
    subtotal = sum(i["price"] * i["qty"] for i in st.session_state.cart)
    tax = subtotal * 0.05
    total = subtotal + tax
    receipt_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Deduct stock
    for item in st.session_state.cart:
        for prod in st.session_state.products:
            if prod["id"] == item["id"]:
                prod["stock"] -= item["qty"]
    
    sale_record = {
        "receipt_id": receipt_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": customer_name if customer_name else "Walk-in Customer",
        "items": list(st.session_state.cart),
        "subtotal": subtotal,
        "tax": tax,
        "total": total
    }
    
    st.session_state.sales_history.insert(0, sale_record)
    st.session_state.cart = []
    return sale_record

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💊 PharmaCare POS")
low_stock_list = get_low_stock_items()
if low_stock_list:
    st.sidebar.warning(f"⚠️ **{len(low_stock_list)} Items Low in Stock!**")

nav = st.sidebar.radio(
    "Navigation Menu",
    ["🛒 POS / Billing", "📊 Dashboard", "📦 Inventory Management", "🧾 Sales & Receipts"]
)

# --- POPUP LOW STOCK REMINDER DIALOG ---
@st.dialog("🚨 Low Stock Warning Alert")
def show_low_stock_dialog():
    st.write("The following pharmacy products have reached critical reorder levels:")
    low_items = get_low_stock_items()
    if low_items:
        df_low = pd.DataFrame(low_items)[["name", "category", "stock", "min_threshold"]]
        df_low.columns = ["Medicine Name", "Category", "Current Stock", "Min Threshold"]
        st.dataframe(df_low, use_container_width=True)
    else:
        st.success("All product stock levels are currently healthy!")
    if st.button("Close Alert"):
        st.rerun()

if st.sidebar.button("🔔 Check Low Stock Popup"):
    show_low_stock_dialog()

# ==========================================
# PAGE 1: POS / BILLING & CART
# ==========================================
if nav == "🛒 POS / Billing":
    st.title("🛒 Pharmacy Point of Sale (POS)")
    
    # Low stock alert banner on top of POS
    if low_stock_list:
        st.error(f"⚠️ **Attention:** {len(low_stock_list)} item(s) are below their reorder threshold! Check sidebar alert.")

    col_catalog, col_cart = st.columns([2, 1])

    with col_catalog:
        st.subheader("Medicine Catalog")
        
        # Filters
        c1, c2 = st.columns([2, 1])
        search_query = c1.text_input("🔍 Search Medicine or SKU", "")
        categories = ["All"] + list(set(p["category"] for p in st.session_state.products))
        selected_category = c2.selectbox("Filter Category", categories)

        # Filter products
        filtered_prods = [
            p for p in st.session_state.products
            if (selected_category == "All" or p["category"] == selected_category)
            and (search_query.lower() in p["name"].lower())
        ]

        # Product Grid Layout (3 items per row)
        grid_cols = st.columns(3)
        for idx, prod in enumerate(filtered_prods):
            col = grid_cols[idx % 3]
            with col:
                with st.container(border=True):
                    st.image(prod["image"], use_container_width=True)
                    st.caption(f"**{prod['category']}**")
                    st.markdown(f"##### {prod['name']}")
                    if prod["rx_required"]:
                        st.caption("🔴 **Rx Required**")
                    st.markdown(f"**Price:** `${prod['price']:.2f}`")
                    
                    if prod["stock"] <= 0:
                        st.error("Out of Stock")
                        st.button("Add", key=f"add_{prod['id']}", disabled=True)
                    else:
                        st.info(f"In Stock: {prod['stock']}")
                        if st.button(f"➕ Add to Cart", key=f"add_{prod['id']}", use_container_width=True):
                            add_to_cart(prod["id"])
                            st.rerun()

    with col_cart:
        st.subheader("Current Cart Order")
        customer_name = st.text_input("Customer Name / Phone", "Walk-in Customer")
        
        if not st.session_state.cart:
            st.info("Your cart is currently empty.")
        else:
            cart_data = []
            for item in st.session_state.cart:
                cart_data.append({
                    "Medicine": item["name"],
                    "Price": f"${item['price']:.2f}",
                    "Qty": item["qty"],
                    "Total": f"${(item['price'] * item['qty']):.2f}"
                })
            
            st.dataframe(pd.DataFrame(cart_data), use_container_width=True, hide_index=True)
            
            subtotal = sum(i["price"] * i["qty"] for i in st.session_state.cart)
            tax = subtotal * 0.05
            total = subtotal + tax
            
            st.markdown("---")
            st.write(f"**Subtotal:** ${subtotal:.2f}")
            st.write(f"**Tax (5%):** ${tax:.2f}")
            st.markdown(f"### **Total: ${total:.2f}**")

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
                
            if col_btn2.button("✅ Checkout & Print Receipt", type="primary", use_container_width=True):
                receipt = process_checkout(customer_name)
                if receipt:
                    st.success(f"Sale Completed! Receipt #{receipt['receipt_id']}")
                    
                    # Printable Receipt Display
                    st.markdown("### 🧾 Receipt Preview")
                    receipt_text = f\"\"\"
                    **PHARMACARE PHARMACY**
                    123 Health Ave, Medical District
                    ---------------------------------
                    Receipt ID: {receipt['receipt_id']}
                    Date: {receipt['date']}
                    Customer: {receipt['customer']}
                    ---------------------------------
                    \"\"\"
                    for item in receipt['items']:
                        receipt_text += f"\\n- {item['name']} x {item['qty']} = ${item['price']*item['qty']:.2f}"
                    
                    receipt_text += f\"\"\"
                    ---------------------------------
                    Subtotal: ${receipt['subtotal']:.2f}
                    Tax (5%): ${receipt['tax']:.2f}
                    TOTAL PAID: ${receipt['total']:.2f}
                    ---------------------------------
                    Thank you for choosing PharmaCare!
                    \"\"\"
                    st.code(receipt_text, language="markdown")
                    st.download_button(
                        label="💾 Download Receipt Text",
                        data=receipt_text,
                        file_name=f"Receipt_{receipt['receipt_id']}.txt",
                        mime="text/plain"
                    )

# ==========================================
# PAGE 2: DASHBOARD & ANALYTICS
# ==========================================
elif nav == "📊 Dashboard":
    st.title("📊 Pharmacy Analytics & Metrics")
    
    total_revenue = sum(s["total"] for s in st.session_state.sales_history)
    total_orders = len(st.session_state.sales_history)
    total_skus = len(st.session_state.products)
    low_stock_count = len(get_low_stock_items())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"${total_revenue:.2f}", delta="Live Sales")
    m2.metric("Orders Processed", total_orders)
    m3.metric("Total Medicine SKUs", total_skus)
    m4.metric("Low Stock Alerts", low_stock_count, delta="-Needs Restock" if low_stock_count > 0 else "Healthy", delta_color="inverse")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Inventory Stock by Category")
        df_prods = pd.DataFrame(st.session_state.products)
        if not df_prods.empty:
            cat_fig = px.pie(df_prods, names="category", values="stock", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(cat_fig, use_container_width=True)

    with c2:
        st.subheader("Sales History Summary")
        if st.session_state.sales_history:
            df_sales = pd.DataFrame(st.session_state.sales_history)
            line_fig = px.line(df_sales, x="date", y="total", markers=True, title="Recent Transactions Revenue ($)")
            st.plotly_chart(line_fig, use_container_width=True)
        else:
            st.info("No completed sales transactions yet.")

# ==========================================
# PAGE 3: INVENTORY MANAGEMENT
# ==========================================
elif nav == "📦 Inventory Management":
    st.title("📦 Medicine Inventory Management")

    st.subheader("Add / Update Product")
    with st.form("add_product_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        prod_name = f1.text_input("Medicine Name*", "Azithromycin 250mg")
        category = f2.selectbox("Category*", ["Antibiotics", "Pain Relief", "Vitamins", "First Aid", "General"])
        price = f3.number_input("Price ($)*", min_value=0.1, value=15.00, step=0.5)

        f4, f5, f6 = st.columns(3)
        stock = f4.number_input("Stock Quantity*", min_value=0, value=50)
        min_threshold = f5.number_input("Min Alert Threshold*", min_value=1, value=10)
        rx_required = f6.checkbox("Prescription Required (Rx)")

        image_url = st.text_input("Image URL", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=400&q=80")

        submitted = st.form_submit_button("➕ Save Medicine to Inventory", type="primary")
        if submitted:
            new_id = f"P{len(st.session_state.products) + 1:03d}"
            st.session_state.products.append({
                "id": new_id,
                "name": prod_name,
                "category": category,
                "price": price,
                "stock": stock,
                "min_threshold": min_threshold,
                "rx_required": rx_required,
                "image": image_url
            })
            st.success(f"Added {prod_name} to inventory!")
            st.rerun()

    st.markdown("---")
    st.subheader("Current Stock Table")
    df_inv = pd.DataFrame(st.session_state.products)
    
    # Highlight low stock items
    st.dataframe(
        df_inv[["id", "name", "category", "price", "stock", "min_threshold", "rx_required"]],
        use_container_width=True
    )

    # Quick Restock Tool
    st.subheader("⚡ Quick Restock Tool")
    r1, r2 = st.columns([2, 1])
    selected_prod_id = r1.selectbox("Select Medicine to Restock", [f"{p['id']} - {p['name']}" for p in st.session_state.products])
    restock_qty = r2.number_input("Add Quantity", min_value=1, value=20)
    
    if st.button("Restock Stock Now"):
        prod_id = selected_prod_id.split(" - ")[0]
        for p in st.session_state.products:
            if p["id"] == prod_id:
                p["stock"] += restock_qty
                st.success(f"Added {restock_qty} units to {p['name']}. New Stock: {p['stock']}")
                st.rerun()

# ==========================================
# PAGE 4: SALES HISTORY & RECEIPTS
# ==========================================
elif nav == "🧾 Sales & Receipts":
    st.title("🧾 Completed Sales Log & Receipts")

    if not st.session_state.sales_history:
        st.info("No completed sales transactions logged.")
    else:
        df_history = pd.DataFrame(st.session_state.sales_history)
        st.dataframe(df_history[["receipt_id", "date", "customer", "subtotal", "tax", "total"]], use_container_width=True)

        st.subheader("Search Receipt Details")
        selected_receipt_id = st.selectbox("Select Receipt ID", [s["receipt_id"] for s in st.session_state.sales_history])
        
        selected_sale = next((s for s in st.session_state.sales_history if s["receipt_id"] == selected_receipt_id), None)
        if selected_sale:
            st.write(f"**Customer:** {selected_sale['customer']}")
            st.write(f"**Date:** {selected_sale['date']}")
            st.write(f"**Total Paid:** ${selected_sale['total']:.2f}")
            st.markdown("#### Item Breakdown:")
            st.dataframe(pd.DataFrame(selected_sale["items"])[["name", "price", "qty"]], use_container_width=True)
"""
with open('app.py', 'w') as f:
    f.write(app_code)

print("Files created successfully.")