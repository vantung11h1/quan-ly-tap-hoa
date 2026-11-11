import csv
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

DB_NAME = "taphoa.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Table Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            buy_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5
        )
    """)
    # Table Sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_code TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT DEFAULT 'Tiền mặt',
            note TEXT
        )
    """)

    # Insert sample data if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("SP001", "Gạo Tám Thái 5kg", "Đồ khô", "Túi", 140000, 165000, 15, 5),
            ("SP002", "Dầu ăn Simply 1L", "Gia vị", "Chai", 52000, 60000, 20, 5),
            (
                "SP003",
                "Mì Hảo Hảo Tôm Chua Cay",
                "Đồ ăn nhanh",
                "Thùng",
                108000,
                120000,
                10,
                3,
            ),
            (
                "SP004",
                "Pin AA Panasonic",
                "Mặt hàng khác",
                "Vỉ",
                15000,
                22000,
                8,
                10,
            ),
            (
                "SP005",
                "Khẩu trang y tế 4 lớp",
                "Mặt hàng khác",
                "Hộp",
                22000,
                35000,
                12,
                5,
            ),
            (
                "SP006",
                "Thẻ cào Viettel 100k",
                "Mặt hàng khác",
                "Thẻ",
                97000,
                100000,
                20,
                5,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO products (code, name, category, unit, buy_price, sell_price, stock, min_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_data,
        )

    conn.commit()
    conn.close()


class TapHoaApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(
            "Phần Mềm Quản Lý Tạp Hóa - Hỗ Trợ Máy Quét Mã Vạch (Convenience"
            " Store)"
        )
        self.geometry("1100x720")

        # =========================================================
        # 🎯 HIỂN THỊ LOGO / ICON CỬA SỔ ỨNG DỤNG
        # Tự động nạp file 'app_icon.ico' nếu có trong cùng thư mục
        # =========================================================
        if os.path.exists("app_icon.ico"):
            try:
                self.iconbitmap("app_icon.ico")
            except Exception:
                pass

        # Configure Style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#1F4E79",
            foreground="white",
        )
        self.style.configure("Treeview", font=("Arial", 10), rowheight=25)

        # Cart memory
        self.cart_items = []
        self.current_sale_product = None

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.tab_sales = ttk.Frame(self.notebook)
        self.tab_products = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(
            self.tab_sales, text="🛒 Bắn Mã / Bán Hàng Trực Tiếp"
        )
        self.notebook.add(self.tab_products, text="📦 Quản Lý Kho & Mã Vạch")
        self.notebook.add(self.tab_reports, text="📊 Báo Cáo & Xuất File")

        self.setup_tab_sales()
        self.setup_tab_products()
        self.setup_tab_reports()

        # Auto focus on barcode entry at startup
        self.ent_sale_code.focus_set()

    # ----------------------------------------------------
    # TAB 1: SALES & BARCODE SCANNER (BẮN MÃ VẠCH BÁN HÀNG)
    # ----------------------------------------------------
    def setup_tab_sales(self):
        # Top Frame: Quét mã vạch
        frame_input = ttk.LabelFrame(
            self.tab_sales,
            text=" 1. Quét / Bắn mã vạch sản phẩm (Hoặc nhập mã) ",
        )
        frame_input.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            frame_input, text="📷 Mã Vạch (Barcode):", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, padx=5, pady=8)
        self.ent_sale_code = ttk.Entry(
            frame_input, width=18, font=("Arial", 11)
        )
        self.ent_sale_code.grid(row=0, column=1, padx=5, pady=8)

        # Bắt sự kiện bắn mã (phím Enter từ súng quét) hoặc gõ phím
        self.ent_sale_code.bind("<KeyRelease>", self.on_sale_input_change)
        self.ent_sale_code.bind("<Return>", self.on_barcode_scan_enter)

        ttk.Label(frame_input, text="Tên SP:").grid(
            row=0, column=2, padx=5, pady=8
        )
        self.lbl_sale_name = ttk.Label(
            frame_input,
            text="---",
            font=("Arial", 10, "bold"),
            foreground="navy",
            width=25,
        )
        self.lbl_sale_name.grid(row=0, column=3, padx=5, pady=8)

        ttk.Label(frame_input, text="Đơn giá:").grid(
            row=0, column=4, padx=5, pady=8
        )
        self.lbl_sale_price = ttk.Label(
            frame_input,
            text="0 đ",
            font=("Arial", 10, "bold"),
            foreground="green",
            width=12,
        )
        self.lbl_sale_price.grid(row=0, column=5, padx=5, pady=8)

        ttk.Label(frame_input, text="Số Lượng:").grid(
            row=1, column=0, padx=5, pady=5
        )
        self.ent_sale_qty = ttk.Entry(frame_input, width=18)
        self.ent_sale_qty.insert(0, "1")
        self.ent_sale_qty.grid(row=1, column=1, padx=5, pady=5)
        self.ent_sale_qty.bind("<KeyRelease>", self.on_sale_input_change)
        self.ent_sale_qty.bind(
            "<Return>", lambda e: self.add_to_cart()
        )  # Nhấn Enter ở số lượng cũng thêm giỏ

        ttk.Label(frame_input, text="Thành Tiền Món:").grid(
            row=1, column=2, padx=5, pady=5
        )
        self.lbl_item_total = ttk.Label(
            frame_input,
            text="0 đ",
            font=("Arial", 11, "bold"),
            foreground="darkred",
        )
        self.lbl_item_total.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Button(
            frame_input, text="➕ Thêm Vào Giỏ (Enter)", command=self.add_to_cart
        ).grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky="ew")

        # Middle Frame: Giỏ Hàng
        frame_cart = ttk.LabelFrame(
            self.tab_sales, text=" 2. Danh sách mặt hàng trong hóa đơn "
        )
        frame_cart.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("code", "name", "price", "qty", "total")
        self.tree_cart = ttk.Treeview(
            frame_cart, columns=cols, show="headings", height=8
        )

        headings = [
            ("code", "Mã Vạch / Mã SP"),
            ("name", "Tên Sản Phẩm"),
            ("price", "Đơn Giá"),
            ("qty", "Số Lượng"),
            ("total", "Thành Tiền"),
        ]

        for col, h in headings:
            self.tree_cart.heading(col, text=h)
            width = 220 if col == "name" else 120
            self.tree_cart.column(col, width=width, anchor=tk.CENTER)

        self.tree_cart.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5
        )

        btn_cart_frame = ttk.Frame(frame_cart)
        btn_cart_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Button(
            btn_cart_frame, text="❌ Xóa Món Chọn", command=self.remove_from_cart
        ).pack(fill=tk.X, pady=5)
        ttk.Button(
            btn_cart_frame, text="🧹 Xóa Sạch Giỏ", command=self.clear_cart
        ).pack(fill=tk.X, pady=5)

        # Bottom Frame: Thanh Toán
        frame_pay = ttk.LabelFrame(
            self.tab_sales, text=" 3. Thanh toán đơn hàng "
        )
        frame_pay.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            frame_pay, text="TỔNG CỘNG ĐƠN HÀNG:", font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, padx=10)
        self.lbl_grand_total = ttk.Label(
            frame_pay,
            text="0 VNĐ",
            font=("Arial", 16, "bold"),
            foreground="red",
        )
        self.lbl_grand_total.pack(side=tk.LEFT, padx=10)

        ttk.Label(frame_pay, text="Hình thức TT:").pack(
            side=tk.LEFT, padx=(20, 5)
        )
        self.cbo_pay = ttk.Combobox(
            frame_pay,
            values=["Tiền mặt", "Chuyển khoản / VietQR", "Ghi nợ"],
            width=18,
        )
        self.cbo_pay.set("Tiền mặt")
        self.cbo_pay.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            frame_pay,
            text="💳 THANH TOÁN & HOÀN TẤT",
            command=self.process_checkout,
        ).pack(side=tk.RIGHT, padx=15, pady=10, ipady=5)

    def on_sale_input_change(self, event=None):
        code = self.ent_sale_code.get().strip()
        if not code:
            self.lbl_sale_name.config(text="---")
            self.lbl_sale_price.config(text="0 đ")
            self.lbl_item_total.config(text="0 đ")
            self.current_sale_product = None
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, sell_price, stock FROM products WHERE code=?",
            (code,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            name, price, stock = row
            self.lbl_sale_name.config(text=f"{name} (Kho: {stock})")
            self.lbl_sale_price.config(text=f"{price:,.0f} đ")
            self.current_sale_product = (code, name, price, stock)

            try:
                qty = int(self.ent_sale_qty.get().strip())
                if qty > 0:
                    self.lbl_item_total.config(text=f"{qty * price:,.0f} đ")
                else:
                    self.lbl_item_total.config(text="0 đ")
            except ValueError:
                self.lbl_item_total.config(text="0 đ")
        else:
            self.lbl_sale_name.config(text="❌ Không tìm thấy mã")
            self.lbl_sale_price.config(text="0 đ")
            self.lbl_item_total.config(text="0 đ")
            self.current_sale_product = None

    def on_barcode_scan_enter(self, event=None):
        if self.current_sale_product:
            self.add_to_cart()
        else:
            messagebox.showwarning(
                "Cảnh báo",
                "Mã vạch chưa có trong kho! Vui lòng thêm sản phẩm vào hệ"
                " thống trước.",
            )

    def add_to_cart(self):
        if not self.current_sale_product:
            messagebox.showerror(
                "Lỗi", "Vui lòng quét hoặc nhập đúng Mã sản phẩm!"
            )
            return

        code, name, price, stock = self.current_sale_product
        try:
            qty = int(self.ent_sale_qty.get().strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số lượng phải là số nguyên > 0!")
            return

        if qty > stock:
            messagebox.showwarning(
                "Cảnh báo", f"Tồn kho không đủ (Hiện còn {stock})!"
            )
            return

        found = False
        for item in self.cart_items:
            if item["code"] == code:
                if item["qty"] + qty > stock:
                    messagebox.showwarning(
                        "Cảnh báo",
                        f"Tổng số lượng trong giỏ vượt quá tồn kho"
                        f" ({stock})!",
                    )
                    return
                item["qty"] += qty
                item["total"] = item["qty"] * price
                found = True
                break

        if not found:
            self.cart_items.append({
                "code": code,
                "name": name,
                "price": price,
                "qty": qty,
                "total": qty * price,
            })

        self.update_cart_tree()

        self.ent_sale_code.delete(0, tk.END)
        self.ent_sale_qty.delete(0, tk.END)
        self.ent_sale_qty.insert(0, "1")
        self.on_sale_input_change()
        self.ent_sale_code.focus_set()

    def update_cart_tree(self):
        for item in self.tree_cart.get_children():
            self.tree_cart.delete(item)

        grand_total = 0
        for item in self.cart_items:
            self.tree_cart.insert(
                "",
                tk.END,
                values=(
                    item["code"],
                    item["name"],
                    f"{item['price']:,.0f}",
                    item["qty"],
                    f"{item['total']:,.0f}",
                ),
            )
            grand_total += item["total"]

        self.lbl_grand_total.config(text=f"{grand_total:,.0f} VNĐ")

    def remove_from_cart(self):
        selected = self.tree_cart.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn món cần xóa!")
            return
        idx = self.tree_cart.index(selected[0])
        del self.cart_items[idx]
        self.update_cart_tree()
        self.ent_sale_code.focus_set()

    def clear_cart(self):
        self.cart_items.clear()
        self.update_cart_tree()
        self.ent_sale_code.focus_set()

    def print_receipt(self, receipt_data):
        """Tạo và xử lý in hóa đơn chuẩn phong cách Cửa hàng tiện lợi (Mini Mart)"""
        receipt_lines = []
        receipt_lines.append("        CUA HANG TIEN LOI CONVENI        ")
        receipt_lines.append("      ĐC: 123 Đường ABC, Quận XYZ        ")
        receipt_lines.append("        HOTLINE: 1900 1234 56           ")
        receipt_lines.append("----------------------------------------")
        receipt_lines.append(f"Mã HD: #{receipt_data['invoice_id']}")
        receipt_lines.append(f"Thời gian: {receipt_data['date']}")
        receipt_lines.append(f"Hình thức TT: {receipt_data['payment_method']}")
        receipt_lines.append("----------------------------------------")
        receipt_lines.append(f"{'TEN SP':<18} {'SL':<3} {'GIA':<7} {'TIEN':<8}")
        receipt_lines.append("----------------------------------------")

        for item in receipt_data["items"]:
            name = item["name"][:18]
            qty = item["qty"]
            price = f"{item['price']:,.0f}"
            total = f"{item['total']:,.0f}"
            receipt_lines.append(f"{name:<18} {qty:<3} {price:<7} {total:<8}")

        receipt_lines.append("----------------------------------------")
        receipt_lines.append(
            f"TỔNG CỘNG: {receipt_data['grand_total']:>27} VNĐ"
        )
        receipt_lines.append("----------------------------------------")
        receipt_lines.append("        XIN CÁM ƠN & HẸN GẶP LẠI!       ")
        receipt_lines.append("               (VĂN TÙNG)           ")
        receipt_lines.append("\n\n")

        receipt_text = "\n".join(receipt_lines)

        try:
            file_name = f"hoadon_{receipt_data['invoice_id']}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(receipt_text)

            # Mở cửa sổ xem trước hóa đơn (Preview Window)
            preview_win = tk.Toplevel(self)
            preview_win.title(f"Hóa đơn #{receipt_data['invoice_id']}")
            preview_win.geometry("400x520")

            txt_preview = tk.Text(
                preview_win, font=("Courier New", 10), bg="#f9f9f9"
            )
            txt_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            txt_preview.insert(tk.END, receipt_text)
            txt_preview.config(state=tk.DISABLED)

            btn_frame = ttk.Frame(preview_win)
            btn_frame.pack(fill=tk.X, padx=10, pady=5)

            def do_print_action():
                messagebox.showinfo(
                    "Máy in",
                    "Đã gửi lệnh in hóa đơn đến máy in mặc định của hệ thống!",
                )
                preview_win.destroy()

            ttk.Button(
                btn_frame, text="🖨️ In Hóa Đơn Ngay", command=do_print_action
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            ttk.Button(
                btn_frame, text="Đóng", command=preview_win.destroy
            ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

        except Exception as e:
            messagebox.showerror(
                "Lỗi in", f"Không thể khởi tạo hóa đơn: {str(e)}"
            )

    def process_checkout(self):
        if not self.cart_items:
            messagebox.showerror(
                "Lỗi", "Giỏ hàng đang trống! Hãy bắn mã vạch để chọn hàng."
            )
            return

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pay_method = self.cbo_pay.get()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        for item in self.cart_items:
            cursor.execute(
                """
                INSERT INTO sales (date, product_code, quantity, price, total, payment_method)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    date_str,
                    item["code"],
                    item["qty"],
                    item["price"],
                    item["total"],
                    pay_method,
                ),
            )

            cursor.execute(
                "UPDATE products SET stock = stock - ? WHERE code = ?",
                (item["qty"], item["code"]),
            )

        conn.commit()

        # Lấy ID hóa đơn vừa thêm vào CSDL để in
        cursor.execute("SELECT last_insert_rowid()")
        invoice_id = cursor.fetchone()[0]
        conn.close()

        grand_total_str = self.lbl_grand_total.cget("text").replace(" VNĐ", "")
        receipt_data = {
            "invoice_id": invoice_id,
            "date": date_str,
            "payment_method": pay_method,
            "items": list(self.cart_items),
            "grand_total": grand_total_str,
        }

        messagebox.showinfo(
            "Thành công",
            f"Thanh toán đơn hàng thành công!\nTổng tiền:"
            f" {self.lbl_grand_total.cget('text')}",
        )

        # Kích hoạt tính năng xem trước & in hóa đơn tự động
        self.print_receipt(receipt_data)

        self.clear_cart()
        self.load_products()
        self.ent_sale_code.focus_set()

    # ----------------------------------------------------
    # TAB 2: PRODUCT & BARCODE MANAGEMENT (THÊM / QUẢN LÝ MÃ VẠCH)
    # ----------------------------------------------------
    def setup_tab_products(self):
        frame_form = ttk.LabelFrame(
            self.tab_products,
            text=" Thông tin sản phẩm (Đặt con trỏ vào Mã SP rồi bắn súng quét) ",
        )
        frame_form.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame_form, text="📷 Mã Vạch / SP:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.ent_code = ttk.Entry(frame_form, width=15)
        self.ent_code.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Tên SP:").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W
        )
        self.ent_name = ttk.Entry(frame_form, width=25)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Nhóm Hàng:").grid(
            row=0, column=4, padx=5, pady=5, sticky=tk.W
        )
        self.cbo_cat = ttk.Combobox(
            frame_form,
            values=[
                "Tạp hóa chung",
                "Gia vị",
                "Nước giải khát",
                "Đồ khô",
                "Mặt hàng khác",
            ],
            width=15,
        )
        self.cbo_cat.set("Tạp hóa chung")
        self.cbo_cat.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(frame_form, text="Đơn Vị:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.ent_unit = ttk.Entry(frame_form, width=15)
        self.ent_unit.insert(0, "Cái")
        self.ent_unit.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Giá Nhập:").grid(
            row=1, column=2, padx=5, pady=5, sticky=tk.W
        )
        self.ent_buy = ttk.Entry(frame_form, width=25)
        self.ent_buy.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Giá Bán:").grid(
            row=1, column=4, padx=5, pady=5, sticky=tk.W
        )
        self.ent_sell = ttk.Entry(frame_form, width=15)
        self.ent_sell.grid(row=1, column=5, padx=5, pady=5)

        ttk.Label(frame_form, text="Tồn Kho:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.ent_stock = ttk.Entry(frame_form, width=15)
        self.ent_stock.insert(0, "10")
        self.ent_stock.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Cảnh Báo Tồn:").grid(
            row=2, column=2, padx=5, pady=5, sticky=tk.W
        )
        self.ent_min = ttk.Entry(frame_form, width=25)
        self.ent_min.insert(0, "5")
        self.ent_min.grid(row=2, column=3, padx=5, pady=5)

        btn_frame = ttk.Frame(frame_form)
        btn_frame.grid(row=2, column=4, columnspan=2, pady=5)

        ttk.Button(
            btn_frame, text="💾 Lưu / Thêm SP", command=self.save_product
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Xóa", command=self.delete_product).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            btn_frame, text="🧹 Làm Mới", command=self.clear_product_inputs
        ).pack(side=tk.LEFT, padx=5)

        cols = (
            "id",
            "code",
            "name",
            "category",
            "unit",
            "buy_price",
            "sell_price",
            "stock",
            "min_stock",
            "status",
        )
        self.tree_prod = ttk.Treeview(
            self.tab_products, columns=cols, show="headings", height=15
        )

        headings = [
            ("id", "ID"),
            ("code", "Mã Vạch / SP"),
            ("name", "Tên Sản Phẩm"),
            ("category", "Nhóm Hàng"),
            ("unit", "Đơn Vị"),
            ("buy_price", "Giá Nhập"),
            ("sell_price", "Giá Bán"),
            ("stock", "Tồn Kho"),
            ("min_stock", "Cảnh Báo"),
            ("status", "Trạng Thái"),
        ]

        for col, h in headings:
            self.tree_prod.heading(col, text=h)
            width = 130 if col in ["code", "name", "category"] else 75
            self.tree_prod.column(col, width=width, anchor=tk.CENTER)

        self.tree_prod.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree_prod.bind("<<TreeviewSelect>>", self.on_product_select)

        self.load_products()

    def load_products(self):
        for item in self.tree_prod.get_children():
            self.tree_prod.delete(item)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, code, name, category, unit, buy_price, sell_price,"
            " stock, min_stock FROM products"
        )
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            p_id, code, name, cat, unit, buy, sell, stock, min_s = r
            status = "⚠️ Cần nhập" if stock <= min_s else "✅ Bình thường"
            self.tree_prod.insert(
                "",
                tk.END,
                values=(
                    p_id,
                    code,
                    name,
                    cat,
                    unit,
                    f"{buy:,.0f}",
                    f"{sell:,.0f}",
                    stock,
                    min_s,
                    status,
                ),
            )

    def save_product(self):
        code = self.ent_code.get().strip()
        name = self.ent_name.get().strip()
        cat = self.cbo_cat.get().strip()
        unit = self.ent_unit.get().strip()
        try:
            buy = float(self.ent_buy.get() or 0)
            sell = float(self.ent_sell.get() or 0)
            stock = int(self.ent_stock.get() or 0)
            min_s = int(self.ent_min.get() or 5)
        except ValueError:
            messagebox.showerror("Lỗi", "Giá và tồn kho phải là số hợp lệ!")
            return

        if not code or not name:
            messagebox.showerror(
                "Lỗi", "Vui lòng quét Mã Vạch và nhập Tên sản phẩm!"
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO products (code, name, category, unit, buy_price, sell_price, stock, min_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name, category=excluded.category, unit=excluded.unit,
                buy_price=excluded.buy_price, sell_price=excluded.sell_price,
                stock=excluded.stock, min_stock=excluded.min_stock
        """,
            (code, name, cat, unit, buy, sell, stock, min_s),
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Thành công", f"Đã lưu sản phẩm mã: {code}")
        self.clear_product_inputs()
        self.load_products()

    def delete_product(self):
        selected = self.tree_prod.selection()
        if not selected:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn sản phẩm cần xóa!"
            )
            return
        item = self.tree_prod.item(selected[0])
        p_id = item["values"][0]

        if messagebox.askyesno(
            "Xác nhận", "Bạn có chắc chắn muốn xóa sản phẩm này?"
        ):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=?", (p_id,))
            conn.commit()
            conn.close()
            self.load_products()
            self.clear_product_inputs()

    def clear_product_inputs(self):
        self.ent_code.delete(0, tk.END)
        self.ent_name.delete(0, tk.END)
        self.cbo_cat.set("Tạp hóa chung")
        self.ent_unit.delete(0, tk.END)
        self.ent_unit.insert(0, "Cái")
        self.ent_buy.delete(0, tk.END)
        self.ent_sell.delete(0, tk.END)
        self.ent_stock.delete(0, tk.END)
        self.ent_stock.insert(0, "10")
        self.ent_min.delete(0, tk.END)
        self.ent_min.insert(0, "5")
        self.ent_code.focus_set()

    def on_product_select(self, event):
        selected = self.tree_prod.selection()
        if selected:
            val = self.tree_prod.item(selected[0])["values"]
            self.clear_product_inputs()
            self.ent_code.insert(0, val[1])
            self.ent_name.insert(0, val[2])
            self.cbo_cat.set(val[3])
            self.ent_unit.delete(0, tk.END)
            self.ent_unit.insert(0, val[4])
            self.ent_buy.insert(0, str(val[5]).replace(",", ""))
            self.ent_sell.insert(0, str(val[6]).replace(",", ""))
            self.ent_stock.delete(0, tk.END)
            self.ent_stock.insert(0, val[7])
            self.ent_min.delete(0, tk.END)
            self.ent_min.insert(0, val[8])

    # ----------------------------------------------------
    # TAB 3: REPORTS & EXPORT
    # ----------------------------------------------------
    def setup_tab_reports(self):
        frame_rep = ttk.LabelFrame(
            self.tab_reports, text=" XUẤT BÁO CÁO DỮ LIỆU "
        )
        frame_rep.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        lbl_info = ttk.Label(
            frame_rep,
            text="Xuất danh mục sản phẩm và báo cáo bán hàng ra file Excel/CSV.",
            font=("Arial", 11),
        )
        lbl_info.pack(pady=20)

        btn_excel = ttk.Button(
            frame_rep,
            text="📁 Xuất Danh Mục Sản Phẩm & Mã Vạch (Excel/CSV)",
            command=self.export_products_excel,
        )
        btn_excel.pack(pady=10, ipadx=10, ipady=5)

        btn_sales_excel = ttk.Button(
            frame_rep,
            text="📈 Xuất Báo Cáo Bán Hàng (Excel/CSV)",
            command=self.export_sales_excel,
        )
        btn_sales_excel.pack(pady=10, ipadx=10, ipady=5)

    def export_products_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files (Excel)", "*.csv")]
        )
        if file_path:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT code, name, category, unit, buy_price, sell_price,"
                " stock, min_stock FROM products"
            )
            rows = cursor.fetchall()
            conn.close()

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Mã Vạch/SP",
                    "Tên SP",
                    "Nhóm Hàng",
                    "Đơn Vị",
                    "Giá Nhập",
                    "Giá Bán",
                    "Tồn Kho",
                    "Cảnh Báo Tồn",
                ])
                writer.writerows(rows)

            messagebox.showinfo(
                "Thành công", f"Đã xuất file thành công tại:\n{file_path}"
            )

    def export_sales_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files (Excel)", "*.csv")]
        )
        if file_path:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, date, product_code, quantity, price, total,"
                " payment_method FROM sales"
            )
            rows = cursor.fetchall()
            conn.close()

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Mã Đơn",
                    "Thời Gian",
                    "Mã Vạch/SP",
                    "Số Lượng",
                    "Đơn Giá",
                    "Thành Tiền",
                    "Hình Thức TT",
                ])
                writer.writerows(rows)

            messagebox.showinfo(
                "Thành công",
                f"Đã xuất file báo cáo bán hàng tại:\n{file_path}",
            )


if __name__ == "__main__":
    init_db()
    app = TapHoaApp()
    app.mainloop()