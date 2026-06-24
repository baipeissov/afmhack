"use client";

/**
 * Тонкая клиентская обёртка над react-force-graph-2d.
 *
 * Отдаёт наружу экземпляр графа через колбэк onReady(instance), а не через ref —
 * это надёжно работает при подключении через next/dynamic (ssr:false), где
 * проброс ref не гарантирован. Через instance доступны d3Force/zoomToFit и пр.
 */

import { useEffect, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function ForceGraphCanvas({ onReady, ...props }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && onReady) onReady(ref.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <ForceGraph2D ref={ref} {...props} />;
}
