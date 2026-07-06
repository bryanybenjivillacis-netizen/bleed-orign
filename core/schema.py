SCHEMA = """
CREATE TABLE IF NOT EXISTS antinuke_config (
    guild_id BIGINT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS whitelist (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS admin_whitelist (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS welcome_config (
    guild_id BIGINT PRIMARY KEY,
    channel_id BIGINT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS moderation_cases (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fake_permissions (
    guild_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    permission TEXT NOT NULL,
    PRIMARY KEY (guild_id, role_id, permission)
);

CREATE TABLE IF NOT EXISTS command_permissions (
    guild_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, command, role_id)
);

CREATE TABLE IF NOT EXISTS command_roles (
    guild_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, command, role_id)
);

CREATE TABLE IF NOT EXISTS voicemaster_config (
    guild_id BIGINT PRIMARY KEY,
    join_channel_id BIGINT,
    category_id BIGINT
);

CREATE TABLE IF NOT EXISTS voicemaster_channels (
    channel_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    owner_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_config (
    guild_id BIGINT PRIMARY KEY,
    category_id BIGINT,
    support_role_id BIGINT,
    panel_channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS tickets (
    channel_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    open BOOLEAN NOT NULL DEFAULT TRUE
);
"""
