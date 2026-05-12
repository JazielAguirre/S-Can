# DogDex - Contexto del Proyecto y Reglas de Desarrollo

## Descripción General

DogDex es una plataforma web de reconocimiento de razas caninas mediante inteligencia artificial. El sistema permite al usuario capturar o subir una fotografía de un perro para identificar automáticamente su posible raza o mezcla de razas.

El sistema debe devolver:

* Nombre de la raza detectada
* Porcentaje de coincidencia
* Información básica de cuidados
* Temperamento y características generales

El objetivo inicial es construir un MVP funcional y escalable.

---

# Stack Tecnológico

## Frontend

* HTML5
* CSS3
* JavaScript Vanilla (sin frameworks)
* Diseño responsivo mobile-first

## Backend

* Node.js
* Express.js

## Procesamiento de Imágenes

* Multer para subida de archivos
* Validación de formatos y tamaños

## Futuro Modelo IA

El sistema deberá estar preparado para integrar posteriormente:

* TensorFlow.js
* Python API externa
* Modelo CNN entrenado
* APIs de visión artificial

Por ahora, el reconocimiento será simulado mediante respuestas mock.

---

# Arquitectura del Proyecto

El proyecto debe mantenerse separado en:

/frontend
/backend

Nunca mezclar lógica frontend y backend.

Estructura sugerida:

/frontend
/css
/js
/assets
index.html

/backend
/routes
/controllers
/middlewares
/uploads
server.js

---

# Reglas de Desarrollo para Claude Code

## 1. Desarrollo Incremental

No construir toda la aplicación de una sola vez.

Siempre:

* avanzar módulo por módulo
* esperar validación del usuario
* explicar qué hace cada parte antes de continuar

---

## 2. Código Limpio y Escalable

* Usar nombres claros y descriptivos
* Comentar funciones importantes
* Evitar duplicación de código
* Mantener separación de responsabilidades
* Priorizar legibilidad antes que optimización prematura

---

## 3. Restricciones Técnicas

NO usar:

* React
* Vue
* Angular
* TypeScript
* Tailwind
* Bases de datos todavía

Todo debe funcionar inicialmente con:

* HTML
* CSS
* JavaScript puro
* Node.js + Express

---

## 4. Simulación Temporal del Modelo IA

Mientras no exista el modelo real:

El endpoint `/api/detect` debe responder con JSON simulado.

Ejemplo:

```json
{
  "breed": "Golden Retriever",
  "confidence": "95%",
  "care": {
    "exercise": "Alta actividad física",
    "grooming": "Cepillado frecuente",
    "temperament": "Amigable y sociable"
  }
}
```

Las respuestas pueden variar aleatoriamente entre distintas razas.

---

## 5. Manejo de Errores

Implementar validaciones para:

* archivos no válidos
* imágenes corruptas
* archivos demasiado grandes
* ausencia de imagen
* errores del servidor

Siempre devolver mensajes claros al usuario.

---

## 6. Diseño UI/UX

La interfaz debe:

* verse moderna y limpia
* funcionar correctamente en móviles
* usar tarjetas visuales para resultados
* incluir animaciones suaves simples
* priorizar facilidad de uso

---

## 7. Compatibilidad

El sistema debe funcionar correctamente en:

* Ubuntu Linux
* Navegadores modernos
* Dispositivos móviles Android/iPhone
* Escritorio

---

## 8. Objetivo del MVP

El MVP mínimo debe permitir:

1. Subir imagen
2. Enviar imagen al backend
3. Obtener respuesta simulada
4. Mostrar resultado visualmente
5. Manejar errores básicos

No agregar funcionalidades extras sin autorización del usuario.
