-- Task 93: OSB Settings Table Migration
-- OSB (Otizm Spektrum Bozukluğu) kullanıcı ayarları tablosu

BEGIN;

-- OSB Settings table
CREATE TABLE IF NOT EXISTS osb_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Genel OSB modu
    osb_mode_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Tutarlı düzen (Task 93.1)
    consistent_layout_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    layout_type VARCHAR(20) DEFAULT 'default' NOT NULL CHECK (layout_type IN ('default', 'centered', 'wide')),
    predictable_elements BOOLEAN DEFAULT TRUE NOT NULL,

    -- Sabit menü (Task 93.2)
    fixed_navigation_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    navigation_position VARCHAR(20) DEFAULT 'top' NOT NULL CHECK (navigation_position IN ('top', 'left', 'bottom')),
    navigation_variant VARCHAR(20) DEFAULT 'horizontal' NOT NULL CHECK (navigation_variant IN ('horizontal', 'vertical')),

    -- Renk şeması (Task 93.3)
    consistent_colors_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    theme_changes_disabled BOOLEAN DEFAULT TRUE NOT NULL,
    high_contrast_mode BOOLEAN DEFAULT FALSE NOT NULL,

    -- İkonlar (Task 93.4)
    standard_icons_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    show_icon_labels BOOLEAN DEFAULT TRUE NOT NULL,
    icon_size VARCHAR(10) DEFAULT '24' NOT NULL CHECK (icon_size IN ('16', '20', '24', '32', '40', '48')),

    -- Erişilebilirlik
    reduced_motion BOOLEAN DEFAULT TRUE NOT NULL,
    no_animations BOOLEAN DEFAULT FALSE NOT NULL,
    no_shadows BOOLEAN DEFAULT TRUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT uq_osb_settings_user UNIQUE (user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_osb_settings_user_id ON osb_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_osb_settings_osb_mode ON osb_settings(osb_mode_enabled);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_osb_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_osb_settings_updated_at
    BEFORE UPDATE ON osb_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_osb_settings_updated_at();

-- Comments
COMMENT ON TABLE osb_settings IS 'OSB (Otizm Spektrum Bozukluğu) kullanıcı ayarları - Task 93';
COMMENT ON COLUMN osb_settings.osb_mode_enabled IS 'OSB modu aktif mi';
COMMENT ON COLUMN osb_settings.consistent_layout_enabled IS 'Tutarlı düzen aktif mi (Task 93.1)';
COMMENT ON COLUMN osb_settings.fixed_navigation_enabled IS 'Sabit menü aktif mi (Task 93.2)';
COMMENT ON COLUMN osb_settings.consistent_colors_enabled IS 'Tutarlı renkler aktif mi (Task 93.3)';
COMMENT ON COLUMN osb_settings.standard_icons_enabled IS 'Standart ikonlar aktif mi (Task 93.4)';
COMMENT ON COLUMN osb_settings.show_icon_labels IS 'İkon etiketleri göster (OSB için önemli)';

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Task 93 OSB Settings table migration completed successfully';
    RAISE NOTICE 'Table created: osb_settings';
    RAISE NOTICE 'Indexes created: idx_osb_settings_user_id, idx_osb_settings_osb_mode';
END $$;
