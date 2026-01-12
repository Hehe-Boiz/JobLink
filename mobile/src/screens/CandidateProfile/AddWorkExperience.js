import React, { useState } from 'react';
import {
    View,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    TouchableWithoutFeedback,
    Keyboard,
    ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/CandidateProfile/AddWorkExperienceStyles';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';

import MonthYearInput from '../../components/common/MonthYearInput';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const parseDateToPickerValue = (dateInput) => {
    if (!dateInput) return null;
    const d = new Date(dateInput);
    if (isNaN(d.getTime())) return null;
    return {
        month: MONTHS[d.getMonth()],
        year: d.getFullYear()
    };
};

const convertPickerToDate = (pickerValue) => {
    if (!pickerValue) return null;
    const monthIndex = MONTHS.indexOf(pickerValue.month);
    return new Date(pickerValue.year, monthIndex, 1);
};

const AddWorkExperience = ({ navigation, route }) => {
    const initialData = route?.params?.data || {};
    const isEdit = !!initialData.id;

    const [jobTitle, setJobTitle] = useState(initialData.title || '');
    const [company, setCompany] = useState(initialData.company || '');

    const [startDate, setStartDate] = useState(parseDateToPickerValue(initialData.startDate));
    const [endDate, setEndDate] = useState(parseDateToPickerValue(initialData.endDate));

    const [isCurrentPosition, setIsCurrentPosition] = useState(initialData.isCurrentPosition || false);
    const [description, setDescription] = useState(initialData.description || '');

    const [showSheet, setShowSheet] = useState(false);
    const [sheetType, setSheetType] = useState('undo'); // 'undo' | 'remove'

    const hasChanges = () => {
        const initialStart = JSON.stringify(parseDateToPickerValue(initialData.startDate));
        const currentStart = JSON.stringify(startDate);

        const initialEnd = JSON.stringify(parseDateToPickerValue(initialData.endDate));
        const currentEnd = JSON.stringify(endDate);

        return (
            jobTitle !== (initialData.title || '') ||
            company !== (initialData.company || '') ||
            currentStart !== initialStart ||
            currentEnd !== initialEnd ||
            isCurrentPosition !== (initialData.isCurrentPosition || false) ||
            description !== (initialData.description || '')
        );
    };

    const handleBack = () => {
        if (hasChanges()) {
            Keyboard.dismiss();
            setSheetType('undo');
            setShowSheet(true);
        } else {
            navigation?.goBack ? navigation.goBack() : console.log('Go back');
        }
    };

    const handleSave = () => {
        const data = {
            title: jobTitle,
            company,
            startDate: convertPickerToDate(startDate),
            endDate: isCurrentPosition ? null : convertPickerToDate(endDate),
            isCurrentPosition,
            description
        };
        console.log('Saving work experience:', data);
        navigation?.goBack ? navigation.goBack() : console.log('Saved and go back');
    };

    const handleToggleCurrentPosition = () => {
        const newVal = !isCurrentPosition;
        setIsCurrentPosition(newVal);
        if (newVal) {
            setEndDate(null);
        }
    };

    const onConfirmAction = () => {
        setShowSheet(false);
        if (sheetType === 'undo') {
            navigation?.goBack ? navigation.goBack() : console.log('Undo');
        } else {
            console.log('Removing work experience:', initialData.id);
            navigation?.goBack ? navigation.goBack() : console.log('Removed');
        }
    };

    const handleRemovePress = () => {
        Keyboard.dismiss();
        setSheetType('remove');
        setShowSheet(true);
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.keyboardView}
            >
                <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                    <View style={styles.content}>
                        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                            <MaterialCommunityIcons name="arrow-left" size={28} color="#150B3D" />
                        </TouchableOpacity>

                        <CustomText style={styles.title}>
                            {isEdit ? 'Edit work experience' : 'Add work experience'}
                        </CustomText>

                        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

                            {/* Job Title */}
                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Job title</CustomText>
                                <TextInput
                                    style={styles.input}
                                    value={jobTitle}
                                    onChangeText={setJobTitle}
                                    placeholder=""
                                    placeholderTextColor="#AAA6B9"
                                />
                            </View>

                            {/* Company */}
                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Company</CustomText>
                                <TextInput
                                    style={styles.input}
                                    value={company}
                                    onChangeText={setCompany}
                                    placeholder=""
                                    placeholderTextColor="#AAA6B9"
                                />
                            </View>

                            <View style={styles.dateRow}>
                                <View style={{ flex: 1, marginRight: 10 }}>
                                    <MonthYearInput
                                        label="Start date"
                                        value={startDate}
                                        onChange={setStartDate}
                                        placeholder="Select Date"
                                    />
                                </View>

                                <View style={{ flex: 1, marginLeft: 10 }}>
                                    {isCurrentPosition ? (
                                        <View>
                                            <CustomText style={styles.label}>End date</CustomText>
                                            <View style={[styles.input, { backgroundColor: '#F9F9F9', justifyContent: 'center' }]}>
                                                <CustomText style={{ color: '#AAA6B9' }}>Present</CustomText>
                                            </View>
                                        </View>
                                    ) : (
                                        <MonthYearInput
                                            label="End date"
                                            value={endDate}
                                            onChange={setEndDate}
                                            placeholder="Present"
                                        />
                                    )}
                                </View>
                            </View>

                            <TouchableOpacity
                                style={styles.checkboxRow}
                                onPress={handleToggleCurrentPosition}
                                activeOpacity={0.7}
                            >
                                <View style={[styles.checkbox, isCurrentPosition && styles.checkboxChecked]}>
                                    {isCurrentPosition && (
                                        <MaterialCommunityIcons name="check" size={14} color="#FFF"/>
                                    )}
                                </View>
                                <CustomText style={styles.checkboxLabel}>This is my position now</CustomText>
                            </TouchableOpacity>

                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Description</CustomText>
                                <View style={styles.textAreaContainer}>
                                    <TextInput
                                        style={styles.textArea}
                                        value={description}
                                        onChangeText={setDescription}
                                        placeholder="Write additional information here"
                                        placeholderTextColor="#AAA6B9"
                                        multiline
                                        textAlignVertical="top"
                                    />
                                </View>
                            </View>

                        </ScrollView>

                        <View style={styles.buttonContainer}>
                             {isEdit && (
                                <TouchableOpacity
                                    style={styles.removeButton}
                                    onPress={handleRemovePress}
                                    activeOpacity={0.8}
                                >
                                    <CustomText style={styles.removeButtonText}>REMOVE</CustomText>
                                </TouchableOpacity>
                            )}
                            <TouchableOpacity
                                style={styles.saveButton}
                                onPress={handleSave}
                                activeOpacity={0.8}
                            >
                                <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                            </TouchableOpacity>
                        </View>
                    </View>
                </TouchableWithoutFeedback>
            </KeyboardAvoidingView>

            <ConfirmationSheet
                visible={showSheet}
                type={sheetType}
                onClose={() => setShowSheet(false)}
                onConfirm={onConfirmAction}
            />
        </SafeAreaView>
    );
};

export default AddWorkExperience;