\encoding UTF8
-- ADIM 1 — kaynak (kiro2_temp) tarafi: kopyalanacak 14 konuyu CSV olarak ver.
-- Cakisan 4 kod (KIM/FIZ/GEN/MAT) HARIC; onlar canlida zaten var, ESLENECEK.
-- parent_id REMAP: cakisan bir konuya isaret eden ebeveynler canli id'ye cevrilir.

WITH RECURSIVE kk AS (
    SELECT DISTINCT primary_topic_id AS id
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true AND subject_area = 'KIMYA'
),
z AS (
    SELECT th.id, th.parent_id, th.code, th.name_tr, th.name_en, th.description,
           th.meb_code, th.osym_relevance, th.osym_frequency, th.total_questions,
           th.average_difficulty, th.difficulty_level, th.subject_area,
           th.is_active, th.level
    FROM topic_hierarchy th JOIN kk ON kk.id = th.id
    UNION
    SELECT p.id, p.parent_id, p.code, p.name_tr, p.name_en, p.description,
           p.meb_code, p.osym_relevance, p.osym_frequency, p.total_questions,
           p.average_difficulty, p.difficulty_level, p.subject_area,
           p.is_active, p.level
    FROM z JOIN topic_hierarchy p ON p.id = z.parent_id
),
-- canli id esleme tablosu (S232-F'de olculdu)
esleme(kod, canli_id) AS (VALUES
    ('KIM', '72e79276-4795-424c-a262-0edf9a77a23f'),
    ('FIZ', 'c6c72669-267e-47ce-a3d2-8392de050bc7'),
    ('GEN', '9928457b-b653-46d4-8bc1-a0937b1d9836'),
    ('MAT', '259066bd-71fb-420e-85e3-a4e3ad9811fe')
)
SELECT z.id,
       -- parent_id REMAP: ebeveyn cakisan bir konuysa CANLI id'sini yaz
       coalesce(e_par.canli_id, z.parent_id) AS parent_id,
       z.code, z.name_tr, z.name_en, z.description, z.meb_code,
       z.osym_relevance, z.osym_frequency, z.total_questions,
       z.average_difficulty, z.difficulty_level, z.subject_area,
       z.is_active, z.level
FROM z
LEFT JOIN topic_hierarchy par ON par.id = z.parent_id
LEFT JOIN esleme e_par ON e_par.kod = par.code
WHERE z.code NOT IN ('KIM','FIZ','GEN','MAT')   -- cakisanlari DISLA
ORDER BY z.level, z.code;
