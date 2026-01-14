import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { TextInput } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from "./CustomText";

const AppDatePicker = ({ label, value, onDateChange, placeholder = "Chọn ngày...", required = false }) => {
  const [show, setShow] = useState(false);


  const onChange = (event, selectedDate) => {
    if (event.type === 'dismissed') {
      setShow(false);
      return;
    }
    
    setShow(false); 
    if (selectedDate) {
      onDateChange(selectedDate);
    }
  };


  const formatDate = (date) => {
    if (!date) return '';
    return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}`;
  };

  return (
    <View style={styles.container}>

      {label && (
        <CustomText style={styles.label}>
          {label} {required && <Text style={{ color: 'red' }}>*</Text>}
        </CustomText>
      )}

      <TouchableOpacity 
        style={styles.dateBox} 
        onPress={() => setShow(true)}
        activeOpacity={0.7}
      >
        <CustomText style={[styles.valueText, !value && styles.placeholder]}>
          {value ? formatDate(value) : placeholder}
        </CustomText>
        

        <MaterialCommunityIcons name="calendar-month-outline" size={24} color="#AAA6B9" />
      </TouchableOpacity>

      {show && (
        <DateTimePicker
          testID="dateTimePicker"
          value={value || new Date()} 
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={onChange}
          minimumDate={new Date()} 
          accentColor="#130160"  
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#524B6B',
    marginBottom: 8,
  },
  dateBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#EAEAEA',
    borderRadius: 10,
    height: 50, 
    paddingHorizontal: 15,
  },
  valueText: {
    fontSize: 14,
    color: '#130160',
  },
  placeholder: {
    color: '#AAA6B9',
  }
});

export default AppDatePicker;