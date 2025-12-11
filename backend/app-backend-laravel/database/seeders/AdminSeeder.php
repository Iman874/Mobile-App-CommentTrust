<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use App\Models\User;

class AdminSeeder extends Seeder
{
    /**
     * Run the database seeds.
     *
     * Creates default admin account
     */
    public function run(): void
    {
        // Check if admin user already exists
        $adminEmail = 'admin@commenttrust.com';
        $adminUsername = 'admin';

        $existing = User::where('email', $adminEmail)
            ->orWhere('username', $adminUsername)
            ->first();

        if ($existing) {
            $this->command->info('Admin user already exists!');
            $this->command->info('Username: ' . $existing->username);
            $this->command->info('Email: ' . $existing->email);
            return;
        }

        // Create admin user
        $admin = User::create([
            'name' => 'Administrator',
            'username' => $adminUsername,
            'email' => $adminEmail,
            'password' => Hash::make('admin123'), // Change this in production!
            'role' => 1, // Admin role
            'is_guest' => false,
            'api_token' => Str::random(80),
            'api_token_name' => 'admin-token',
            'token_expires_at' => now()->addYears(10), // Long-lived token for admin
            'email_verified_at' => now(),
        ]);

        $this->command->info('✅ Admin user created successfully!');
        $this->command->line('');
        $this->command->info('Login Credentials:');
        $this->command->line('Username: admin');
        $this->command->line('Password: admin123');
        $this->command->line('');
        $this->command->warn('⚠️  IMPORTANT: Change the password after first login!');
    }
}
