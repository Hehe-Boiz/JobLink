import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Chip } from 'react-native-paper';

const ChipSelector = ({ label, options, selectedValue, onSelect }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.chipRow}>
        {options.map((option) => (
          <Chip
            key={option.id || option}
            mode="outlined"
            selected={selectedValue === option}
            onPress={() => onSelect(option.id || option)}
            style={[
              styles.chip,
              selectedValue === (option.id || option) && styles.chipSelected
            ]}
            textStyle={{
              color: selectedValue === (option.id || option) ? '#141414ff' : '#524B6B',
              fontWeight: selectedValue === (option.id || option) ? 'bold' : 'normal'
            }}
            showSelectedOverlay={true}
          >
            {option.name || option}
          </Chip>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#524B6B',
    marginBottom: 8,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: 'white',
    borderColor: '#EAEAEA',
  },
  chipSelected: {
    backgroundColor: '#FF9228',
    borderColor: '#130160',
  }
});

export default ChipSelector;