# Perbaikan Pengiriman Nama Produk ke Laravel

## Masalah
Nama produk tidak terkirim ke Laravel, sehingga kolom `name` pada tabel `products` menjadi `NULL`.

## Akar Penyebab
1. **Flask API (`api.py`)**: Fungsi `_notify_and_wait_laravel()` hanya mengirim `product_id`, `force`, `canonical`, `short_link`, `link`, dan `user_id` ke Laravel tanpa mengirim data produk.
2. **Laravel Controller**: `CommentTrustController.php` hanya mencari nama produk dari `product_trust` data yang diterima, tetapi data ini tidak selalu tersedia.
3. **Data Produk Tidak Dimanfaatkan**: Data lengkap produk tersimpan di `product.json` di Flask, tetapi tidak dikirim ke Laravel.

## Solusi yang Diterapkan

### 1. **Flask Backend (`backend/app-backend-flask/service/api.py`)**
- Modifikasi fungsi `_notify_and_wait_laravel()` untuk membaca `product.json` dari direktori scrap-data
- Ekstrak informasi produk:
  - `product_name` (dari `name` atau `name_prefix`)
  - `shop_name` (dari `shop.name`)
  - `product_data` (full object untuk backup)
- Kirim data produk tambahan dalam payload JSON ke Laravel

**Perubahan:**
```python
# Load product data from product.json
product_data = {}
product_file = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id, 'product.json')
if os.path.exists(product_file):
    with open(product_file, 'r', encoding='utf-8') as f:
        product_data = json.load(f)

# Extract product name
product_name = product_data.get('name') or product_data.get('name_prefix') or 'Unknown Product'
shop_name = product_data.get('shop', {}).get('name') if isinstance(product_data.get('shop'), dict) else ''

# Kirim dalam payload
payload = json.dumps({
    'product_id': product_id,
    'product_name': product_name,
    'shop_name': shop_name,
    'product_data': product_data,
    # ... field lainnya
})
```

### 2. **Laravel Model (`backend/app-backend-laravel/app/Models/Product.php`)**
- Tambahkan `shop_name` ke `$fillable` array untuk memungkinkan mass assignment

### 3. **Laravel Migration** (`database/migrations/2025_12_17_000000_add_shop_name_to_products.php`)
- Buat migration baru untuk menambahkan kolom `shop_name` ke tabel `products`
- Migration ini aman dan hanya menambah kolom jika belum ada

### 4. **Laravel Controller** (`backend/app-backend-laravel/app/Http/Controllers/CommentTrustController.php`)

**a. Tambah logging input:**
```php
Log::info('CommentTrustController::ingest', [
    'product_id' => $productKey,
    'product_name_from_request' => $request->input('product_name'),
    'shop_name_from_request' => $request->input('shop_name'),
]);
```

**b. Implementasi fallback logic untuk mengekstrak nama produk:**
```php
// Prioritas 1: Dari product_data (direkomendasikan)
$productData = $request->input('product_data', []);
if (is_array($productData) && !empty($productData)) {
    $prodName = $productData['name'] ?? $productData['name_prefix'] ?? null;
}

// Prioritas 2: Dari product_name direct field
if (!$prodName) {
    $prodName = $request->input('product_name') ?? null;
}

// Prioritas 3: Dari product_trust (legacy method)
if (!$prodName) {
    $prodName = $pt['product']['name'] ?? null;
}

// Fallback: Unknown Product
if (!$prodName) {
    $prodName = 'Unknown Product';
}
```

**c. Tambah logging verification:**
```php
Log::info("PRODUCT_NAME_EXTRACTION product_id={$productKey}", [
    'product_name' => $prodName,
    'shop_name' => $shopName,
    'from_product_data' => !empty($productData),
    'from_direct_field' => !empty($request->input('product_name')),
    'from_product_trust' => !empty($pt['product']['name'] ?? null),
]);
```

## Instalasi

### 1. Deploy Flask changes
Restart Flask service agar menggunakan kode baru:
```bash
cd backend/app-backend-flask
python main.py
```

### 2. Apply Laravel migration
```bash
cd backend/app-backend-laravel
php artisan migrate
```

### 3. Restart Laravel (jika perlu)
```bash
php artisan serve
```

## Testing

### 1. Monitor logs saat produk di-scrape
**Laravel logs:**
```bash
tail -f storage/logs/laravel.log | grep "PRODUCT_NAME_EXTRACTION"
```

Keluaran yang diharapkan:
```
[timestamp] local.INFO: PRODUCT_NAME_EXTRACTION product_id=12345-67890 {
  "product_name": "Nama Produk Actual",
  "shop_name": "Nama Toko",
  "from_product_data": true,
  "from_direct_field": true,
  "from_product_trust": false
}
```

### 2. Verifikasi database
```php
// Laravel Tinker
php artisan tinker
>>> Product::where('product_key', '12345-67890')->first();
# Harusnya menampilkan name dan shop_name yang terisi
```

### 3. Scrape produk baru
Scrape produk baru dan pastikan nama produk terisi di tabel products.

## Benefit
- ✅ Nama produk akan selalu terisi (tidak akan NULL)
- ✅ Nama toko juga disimpan untuk informasi tambahan
- ✅ Fallback logic memastikan kompatibilitas dengan berbagai sumber data
- ✅ Logging detail memudahkan debugging jika masalah muncul
- ✅ Backward compatible (tetap berfungsi dengan data lama)

## Catatan
- Jika produk sudah tersimpan dengan `name=NULL`, jalankan re-scrape atau force scrape untuk mengupdate nama
- Log `PRODUCT_NAME_EXTRACTION` berguna untuk memverifikasi apakah nama produk berhasil diekstrak dari source mana
