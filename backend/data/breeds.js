// Catálogo de razas simuladas para el MVP.
// Cada entrada sigue la estructura que devolverá el modelo real.
const breeds = [
  {
    breed: 'Golden Retriever',
    care: {
      exercise: 'Alta actividad física diaria',
      grooming: 'Cepillado frecuente, especialmente en muda',
      temperament: 'Amigable, confiable y muy sociable'
    }
  },
  {
    breed: 'Labrador Retriever',
    care: {
      exercise: 'Alta actividad física, disfruta nadar',
      grooming: 'Cepillado semanal, pelo corto de bajo mantenimiento',
      temperament: 'Juguetón, leal y fácil de entrenar'
    }
  },
  {
    breed: 'Border Collie',
    care: {
      exercise: 'Muy alta actividad, necesita estimulación mental',
      grooming: 'Cepillado regular dos veces por semana',
      temperament: 'Inteligente, enérgico e instinto de pastoreo'
    }
  },
  {
    breed: 'Bulldog Francés',
    care: {
      exercise: 'Actividad moderada, sensible al calor extremo',
      grooming: 'Limpieza de pliegues faciales y cepillado mínimo',
      temperament: 'Cariñoso, tranquilo y adaptable a espacios pequeños'
    }
  },
  {
    breed: 'Husky Siberiano',
    care: {
      exercise: 'Alta actividad, diseñado para largas distancias',
      grooming: 'Cepillado intenso en temporada de muda',
      temperament: 'Independiente, vocal y muy activo'
    }
  },
  {
    breed: 'Beagle',
    care: {
      exercise: 'Actividad moderada-alta, olfato muy desarrollado',
      grooming: 'Cepillado semanal y limpieza de orejas frecuente',
      temperament: 'Curioso, alegre y bueno con niños'
    }
  },
  {
    breed: 'Pastor Alemán',
    care: {
      exercise: 'Alta actividad, ideal para trabajo y deporte',
      grooming: 'Cepillado frecuente, muda estacional intensa',
      temperament: 'Leal, protector y altamente entrenable'
    }
  },
  {
    breed: 'Poodle Estándar',
    care: {
      exercise: 'Actividad moderada-alta, muy ágil',
      grooming: 'Corte profesional cada 6-8 semanas',
      temperament: 'Muy inteligente, elegante y sociable'
    }
  }
];

module.exports = breeds;
