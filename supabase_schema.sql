-- =============================================
-- سكربت إنشاء قاعدة البيانات لمتتبع الإنتاجية
-- Productivity Tracker Database Schema
-- =============================================

-- تفعيل Row Level Security
-- Enable Row Level Security

-- جدول ملفات المستخدمين
-- User Profiles Table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    daily_goal INTEGER DEFAULT 100,
    weekly_goal INTEGER DEFAULT 500,
    monthly_goal INTEGER DEFAULT 2000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- تفعيل RLS على جدول الملفات الشخصية
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- سياسات الأمان للملفات الشخصية
CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- =============================================

-- جدول سجلات الإنتاجية
-- Productivity Logs Table
CREATE TABLE IF NOT EXISTS productivity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    time_slot INTEGER NOT NULL CHECK (time_slot >= 0 AND time_slot <= 47),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 4),
    category TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, log_date, time_slot)
);

-- تفعيل RLS على جدول السجلات
ALTER TABLE productivity_logs ENABLE ROW LEVEL SECURITY;

-- سياسات الأمان للسجلات
CREATE POLICY "Users can view their own logs" ON productivity_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own logs" ON productivity_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own logs" ON productivity_logs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own logs" ON productivity_logs
    FOR DELETE USING (auth.uid() = user_id);

-- =============================================

-- جدول الفئات المخصصة
-- Custom Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    color TEXT DEFAULT '#4CAF50',
    icon TEXT DEFAULT '📌',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- تفعيل RLS على جدول الفئات
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

-- سياسات الأمان للفئات
CREATE POLICY "Users can view default and their own categories" ON categories
    FOR SELECT USING (is_default = TRUE OR auth.uid() = user_id);

CREATE POLICY "Users can insert their own categories" ON categories
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own categories" ON categories
    FOR UPDATE USING (auth.uid() = user_id AND is_default = FALSE);

CREATE POLICY "Users can delete their own categories" ON categories
    FOR DELETE USING (auth.uid() = user_id AND is_default = FALSE);

-- =============================================

-- إدخال الفئات الافتراضية
-- Insert Default Categories
INSERT INTO categories (name, name_ar, color, icon, is_default) VALUES
    ('Work', 'العمل', '#2196F3', '💼', TRUE),
    ('Study', 'الدراسة', '#9C27B0', '📚', TRUE),
    ('Health', 'الصحة', '#4CAF50', '🏃', TRUE),
    ('Finance', 'المالية', '#FF9800', '💰', TRUE),
    ('Leisure', 'الترفيه', '#E91E63', '🎮', TRUE),
    ('Personal', 'شخصي', '#00BCD4', '🏠', TRUE),
    ('Social', 'اجتماعي', '#FFEB3B', '👥', TRUE)
ON CONFLICT DO NOTHING;

-- =============================================

-- دالة لإنشاء ملف شخصي تلقائياً عند التسجيل
-- Function to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'display_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- تفعيل الـ Trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================

-- فهارس لتحسين الأداء
-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_productivity_logs_user_date 
    ON productivity_logs(user_id, log_date);

CREATE INDEX IF NOT EXISTS idx_productivity_logs_user_date_slot 
    ON productivity_logs(user_id, log_date, time_slot);

CREATE INDEX IF NOT EXISTS idx_categories_user 
    ON categories(user_id);
