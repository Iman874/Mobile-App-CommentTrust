<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Tag;
use Illuminate\Support\Str;

class TagSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $tags = [
            // Kategori: Kualitas Produk
            [
                'name' => 'Kualitas Baik',
                'description' => 'Produk berkualitas baik dan sesuai deskripsi',
                'category' => 'kualitas',
                'color' => '#4CAF50',
            ],
            [
                'name' => 'Kualitas Jelek',
                'description' => 'Produk berkualitas rendah atau tidak sesuai ekspektasi',
                'category' => 'kualitas',
                'color' => '#F44336',
            ],
            [
                'name' => 'Produk Rusak',
                'description' => 'Produk datang dalam kondisi rusak',
                'category' => 'kualitas',
                'color' => '#D32F2F',
            ],
            [
                'name' => 'Sesuai Deskripsi',
                'description' => 'Produk sesuai dengan deskripsi penjual',
                'category' => 'kualitas',
                'color' => '#66BB6A',
            ],

            // Kategori: Pengiriman
            [
                'name' => 'Pengiriman Cepat',
                'description' => 'Produk dikirim dengan cepat',
                'category' => 'pengiriman',
                'color' => '#2196F3',
            ],
            [
                'name' => 'Pengiriman Lambat',
                'description' => 'Pengiriman memakan waktu lebih lama dari estimasi',
                'category' => 'pengiriman',
                'color' => '#FF9800',
            ],
            [
                'name' => 'Packaging Baik',
                'description' => 'Kemasan produk aman dan rapi',
                'category' => 'pengiriman',
                'color' => '#03A9F4',
            ],
            [
                'name' => 'Packaging Jelek',
                'description' => 'Kemasan produk tidak aman atau rusak',
                'category' => 'pengiriman',
                'color' => '#FF5722',
            ],

            // Kategori: Harga
            [
                'name' => 'Harga Terjangkau',
                'description' => 'Harga produk reasonable dan terjangkau',
                'category' => 'harga',
                'color' => '#8BC34A',
            ],
            [
                'name' => 'Harga Mahal',
                'description' => 'Harga produk terlalu tinggi dibanding kualitas',
                'category' => 'harga',
                'color' => '#E91E63',
            ],
            [
                'name' => 'Harga Kompetitif',
                'description' => 'Harga lebih murah dari kompetitor',
                'category' => 'harga',
                'color' => '#00BCD4',
            ],

            // Kategori: Layanan
            [
                'name' => 'Layanan Baik',
                'description' => 'Customer service responsif dan membantu',
                'category' => 'layanan',
                'color' => '#9C27B0',
            ],
            [
                'name' => 'Layanan Jelek',
                'description' => 'Customer service tidak responsif atau tidak membantu',
                'category' => 'layanan',
                'color' => '#673AB7',
            ],
            [
                'name' => 'Responsif',
                'description' => 'Seller responsif terhadap pertanyaan pembeli',
                'category' => 'layanan',
                'color' => '#512DA8',
            ],

            // Kategori: Produk Spesifik
            [
                'name' => 'Rekomendasi',
                'description' => 'Produk direkomendasikan oleh pembeli',
                'category' => 'rekomendasi',
                'color' => '#FFC107',
            ],
            [
                'name' => 'Tidak Direkomendasikan',
                'description' => 'Produk tidak direkomendasikan',
                'category' => 'rekomendasi',
                'color' => '#FF6F00',
            ],
            [
                'name' => 'Produk Asli',
                'description' => 'Produk original/bergaransi resmi',
                'category' => 'autentisitas',
                'color' => '#1976D2',
            ],
            [
                'name' => 'Produk Palsu',
                'description' => 'Pembeli mencurigai produk palsu/tidak original',
                'category' => 'autentisitas',
                'color' => '#C62828',
            ],
        ];

        foreach ($tags as $tag) {
            Tag::firstOrCreate(
                ['slug' => Str::slug($tag['name'])],
                $tag + ['is_active' => true]
            );
        }
    }
}
