-- D6 gate2c demote: reversible exclusion table. No question_bank writes.
-- Reverse: TRUNCATE gate2c_demoted;  + restore pre-D6 v_safe_for_beta.
CREATE TABLE IF NOT EXISTS gate2c_demoted (
    id varchar PRIMARY KEY,
    reason text NOT NULL,
    demoted_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO gate2c_demoted (id, reason) VALUES ('05aa5884-9e5d-5888-9efc-cc2cd7639eb0', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('07212872-fa7b-56e5-9ed2-e59a1df7ade8', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('08a894e2-c52b-5c71-9dc8-859adaad2168', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('0ad9425d-de99-5971-b8b3-9804e24e5fb9', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('1609b86a-4095-5c15-bb5d-d506ba55dd17', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('1a6f4d48-7975-5436-b9e3-eb7f9b7718c4', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('1e3c37f3-fd86-51d0-9014-344bb75174e7', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('20ed4349-755f-5149-bcc1-9893cd7e1019', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('2a6cd717-8020-5206-850e-62f9777b9385', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('2d9b2001-bbcf-59b9-9ab4-89576e7e8ad7', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('369872f9-df56-59d1-8dfc-6d5b73333f4a', 'opus_degenerate') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('3d2c1e7a-e109-5215-a93c-6b3b30e61b4a', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('5068d395-ee04-5af6-9ef9-46cd2b7b573e', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('52e7bac2-8cc2-5e1c-bbaa-ac1a6c219ba9', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('54fbb852-b81a-5e1e-b796-e315297f8d80', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('5689d23e-e5c3-54c0-904c-11d085169a5f', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('59956bcb-9cc8-5a65-8385-73bec8a61650', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('5ebc870d-0682-55be-bd31-d0f37f72d649', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('607af75e-fedc-56fe-aea2-7e5b01f1f0d6', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('60ea6c90-f79f-5c3a-abcf-3e4657bfbb91', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('619799c2-361b-57ed-8ca1-5d1798e18a52', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('68af507b-eb89-5b34-aacb-4d368f21e01b', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('68dc2943-eda5-525a-9db5-b94b1c2c2df4', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('6c9d84ff-e554-51ec-8abb-73b043f0dba9', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('6fb60574-90e3-56c2-9258-e4abd9287814', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('7330a1a6-9dbe-525d-a4a3-699bbabea13d', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('747c0b27-6c0b-5f90-9a25-8119535c90d6', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('7d4bb29c-8874-593e-a65e-6945e7f3ab75', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('7db046be-981c-5977-b792-824d265eab5a', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('7dfff5c0-da0e-5f1a-af0a-fe12d114c57e', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('7f47c8e0-e49a-55fa-b7a2-1fe4f3c4f458', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('8914dbb9-512e-514c-9919-8da3b4dd44fb', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('89e86c5e-bcbe-5b23-b5a2-2cd7cd7b4d70', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('8b507ab8-1062-5775-bf51-9cf59347c68f', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('8dd6df00-582a-511d-bc2f-3203339cff1e', 'opus_degenerate') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('97fac20a-273e-54fd-98d1-118dc1170b64', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('990e6932-2151-54ec-96a8-0c469c00e559', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('a22455db-f26d-55ac-b281-255165d08b54', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('a4f58131-5fe2-5c86-b7d5-26feac7f257f', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('a98d145c-2b5b-5a7e-bfd2-3c7c86ef1902', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('b4056fcb-4fe7-5557-8ca5-d0f73bee76d7', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('b4a96f1b-a91d-5712-a24d-4e0fe0b3c8db', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('be950d1c-f2a7-52d2-b00e-e5ccdcd88020', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('bea6e749-7bd5-5a7c-912d-d643885f4f5a', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('c109b938-8853-5245-97e1-5991349c643c', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('c47f981c-72ca-5714-88af-bfc961c74170', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('c66b8c15-1fd0-53af-96c7-2ceef60fde0d', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('c7271867-8a8d-5774-9020-7ea3834741b6', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('c8d1fd23-e0a9-5d3b-ab7f-70157ad43582', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('ca87d8b7-59db-526d-a4f6-876363ac1590', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('cb10dbdb-9ea5-5d3a-972b-9cd0c80f84d0', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('cc655fed-2d46-5fd2-ae3a-daf752a22095', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('cf992ac6-601d-5889-bf28-6fcde042e54c', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('d4794038-b24c-53a9-9e0e-96cc9c15bf64', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('d5c17268-f54a-5673-9368-e9f159f6ed1a', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('dcf5b273-d592-5d2e-bd12-07a2a310ba55', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('e1e48664-d4ca-5daf-a61b-9ca692816797', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('e3ed21d0-1d09-50d1-8295-74bb6fa7967e', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('e66e2c7b-b3e3-5fef-ac4a-054e7c0e2d88', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('e9d0aaaf-fff2-5136-9dbc-933720c439e5', 'opus_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('f70d277d-c0d3-5e1e-86b2-108e932ad0a6', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
INSERT INTO gate2c_demoted (id, reason) VALUES ('fb7517a8-494f-5f07-85a7-f05473953673', 'proxy_garble') ON CONFLICT (id) DO NOTHING;
