import React, {useState} from 'react';
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
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/CandidateProfile/AddWorkExperienceStyles';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';

const AddWorkExperience = ({navigation, route}) => {
    const initialData = route?.params?.data || {};
    const isEdit = !!initialData.id;

    const [jobTitle, setJobTitle] = useState(initialData.title || '');
    const [company, setCompany] = useState(initialData.company || '');
    const [startDate, setStartDate] = useState(initialData.startDate || '');
    const [endDate, setEndDate] = useState(initialData.endDate || '');
    const [isCurrentPosition, setIsCurrentPosition] = useState(initialData.isCurrentPosition || false);
    const [description, setDescription] = useState(initialData.description || '');

    const [showSheet, setShowSheet] = useState(false);
    const [sheetType, setSheetType] = useState('undo'); // 'undo' | 'remove'

    const hasChanges = () => {
        return jobTitle !== (initialData.title || '') ||
            company !== (initialData.company || '') ||
            startDate !== (initialData.startDate || '') ||
            endDate !== (initialData.endDate || '') ||
            isCurrentPosition !== (initialData.isCurrentPosition || false) ||
            description !== (initialData.description || '');
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
            startDate,
            endDate: isCurrentPosition ? 'Present' : endDate,
            isCurrentPosition,
            description
        };
        console.log('Saving work experience:', data);
        navigation?.goBack ? navigation.goBack() : console.log('Saved and go back');
    };

    const onConfirmAction = () => {
        setShowSheet(false);

        if (sheetType === 'undo') {
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Undo and go back');
            }
        } else {
            // TODO: Gọi API xóa work experience
            console.log('Removing work experience:', initialData.id);
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Removed and go back');
            }
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
                        <TouchableOpacity
                            onPress={handleBack}
                            style={styles.backButton}
                        >
                            <MaterialCommunityIcons
                                name="arrow-left"
                                size={28}
                                color="#150B3D"
                            />
                        </TouchableOpacity>

                        <CustomText style={styles.title}>
                            {isEdit ? 'Edit work experience' : 'Add work experience'}
                        </CustomText>

                        <ScrollView
                            showsVerticalScrollIndicator={false}
                            contentContainerStyle={styles.scrollContent}
                        >
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
                                <View style={styles.dateInput}>
                                    <CustomText style={styles.label}>Start date</CustomText>
                                    <TouchableOpacity style={styles.input}>
                                        <TextInput
                                            style={styles.dateText}
                                            value={startDate}
                                            onChangeText={setStartDate}
                                            placeholder=""
                                            placeholderTextColor="#AAA6B9"
                                        />
                                    </TouchableOpacity>
                                </View>
                                <View style={styles.dateInput}>
                                    <CustomText style={styles.label}>End date</CustomText>
                                    <TouchableOpacity
                                        style={[styles.input, isCurrentPosition && styles.inputDisabled]}
                                        disabled={isCurrentPosition}
                                    >
                                        <TextInput
                                            style={[styles.dateText, isCurrentPosition && styles.dateTextDisabled]}
                                            value={isCurrentPosition ? 'Present' : endDate}
                                            onChangeText={setEndDate}
                                            placeholder=""
                                            placeholderTextColor="#AAA6B9"
                                            editable={!isCurrentPosition}
                                        />
                                    </TouchableOpacity>
                                </View>
                            </View>

                            <TouchableOpacity
                                style={styles.checkboxRow}
                                onPress={() => setIsCurrentPosition(!isCurrentPosition)}
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