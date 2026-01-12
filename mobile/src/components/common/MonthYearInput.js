import React, {useState} from 'react';
import {View, TouchableOpacity, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from './CustomText';
import MonthYearPickerModal from './MonthYearPickerModal';

const MonthYearInput = ({
                            label,
                            value,
                            onChange,
                            placeholder = "Select Date",
                            required = false,
                        }) => {
    const [modalVisible, setModalVisible] = useState(false);

    const handleSave = (result) => {
        onChange(result);
    };

    const displayValue = value ? `${value.month} ${value.year}` : null;

    return (
        <View style={styles.container}>
            {label && (
                <CustomText style={styles.label}>
                    {label}
                    {required && <CustomText style={styles.required}> *</CustomText>}
                </CustomText>
            )}

            <TouchableOpacity
                style={styles.inputBox}
                onPress={() => setModalVisible(true)}
                activeOpacity={0.7}
            >
                <CustomText style={[styles.inputText, !displayValue && styles.placeholder]}>
                    {displayValue || placeholder}
                </CustomText>

                <MaterialCommunityIcons
                    name="calendar-month-outline"
                    size={22}
                    color="#AAA6B9"
                />
            </TouchableOpacity>

            <MonthYearPickerModal
                visible={modalVisible}
                onClose={() => setModalVisible(false)}
                onSave={handleSave}
                initialValue={value}
                title={label || 'Select Date'}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginBottom: 0,
    },
    label: {
        fontSize: 16,
        fontWeight: '600',
        color: '#524B6B',
        marginBottom: 8,
    },
    required: {
        color: '#FF0000',
    },
    inputBox: {
        height: 50,
        backgroundColor: '#FFFFFF',
        borderRadius: 10,
        paddingHorizontal: 15,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#EAEAEA',
    },
    inputText: {
        fontSize: 14,
        fontWeight: '500',
        color: '#130160',
    },
    placeholder: {
        color: '#AAA6B9',
    },
});

export default MonthYearInput;