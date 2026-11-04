-- 00 · Cuadre del ETL con la fuente
-- Pregunta: ¿los totales cargados concuerdan con los del Excel y qué se excluyó?
-- Usuario: responsable de datos, docente en la sustentación.
-- Técnica: lectura de las tablas de auditoría que llena el ETL en cada ejecución.

SELECT metrica,
       unidad,
       fuente,
       excluido,
       esperado,
       cargado,
       diferencia,
       CASE WHEN cuadra THEN 'Cuadra' ELSE 'NO CUADRA' END AS resultado,
       explicacion
FROM audit.cuadre_cifras
ORDER BY metrica;

-- Efecto de cada regla de limpieza, de mayor a menor número de filas afectadas.
SELECT regla,
       afectados,
       unidad,
       ROUND(100.0 * afectados / NULLIF(SUM(afectados) FILTER (WHERE unidad = 'filas') OVER (), 0), 1) AS pct_del_total_de_filas_afectadas,
       descripcion,
       tratamiento
FROM audit.calidad_datos
ORDER BY afectados DESC, regla;
