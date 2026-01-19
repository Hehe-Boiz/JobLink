import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { TextInput, useTheme } from 'react-native-paper';


const AppInput = ({ 
  label, 
  value, 
  onChangeText, 
  placeholder, 
  required = false, 
  multiline = false,
  numberOfLines = 1,
  keyboardType = 'default',
  icon = null,
  style
}) => {

  return (
    <View style={[styles.container, style]}>

      {label && (
        <Text style={styles.label}>
          {label} {required && <Text style={{ color: 'red' }}>*</Text>}
        </Text>
      )}

  
      <TextInput
        mode="outlined"
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        multiline={multiline}
        numberOfLines={numberOfLines}
        keyboardType={keyboardType}
        style={[styles.input, multiline && styles.textArea]}
        outlineColor="#EAEAEA"
        activeOutlineColor="#130160"
        left={icon ? <TextInput.Icon icon={icon} color="#AAA6B9" /> : null}
        theme={{ roundness: 10 }}
      />
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
  input: {
    backgroundColor: '#FFFFFF',
    fontSize: 14,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  }
});

export default AppInput;