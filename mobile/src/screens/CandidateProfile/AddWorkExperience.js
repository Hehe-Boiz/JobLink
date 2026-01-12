import React, {useState, useRef} from 'react';
import {
    View,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    Modal,
    Dimensions,
    KeyboardAvoidingView,
    Platform,
    TouchableWithoutFeedback,
    Keyboard,
    ScrollView,
    PanResponder,
    Animated
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/CandidateProfile/AddWorkExperienceStyles'

const {height: screenHeight} = Dimensions.get('window');
const AddWorkExperience = ({navigation, route}) => {
    const initialData = route?.params?.data || {};
    const isEdit = !!initialData.id;

    const [jobTitle, setJobTitle] = useState(initialData.title || '');
    const [company, setCompany] = useState(initialData.company || '');
    const [startDate, setStartDate] = useState(initialData.startDate || '');
    const [endDate, setEndDate] = useState(initialData.endDate || '');
    const [isCurrentPosition, setIsCurrentPosition] = useState(initialData.isCurrentPosition || false);
    const [description, setDescription] = useState(initialData.description || '');

    const [showUndoSheet, setShowUndoSheet] = useState(false);

    const translateY = useRef(new Animated.Value(0)).current;

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, gesture) => {
                return Math.abs(gesture.dy) > Math.abs(gesture.dx);
            },
            onPanResponderMove: (_, gesture) => {
                if (gesture.dy > 0) {
                    translateY.setValue(gesture.dy);
                }
            },
            onPanResponderRelease: (_, gesture) => {
                if (gesture.dy > 100) {
                    closeSheet();
                } else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        tension: 100,
                        friction: 10,
                    }).start();
                }
            },
        })
    ).current;

    const hasChanges = () => {
        return jobTitle !== (initialData.title || '') ||
            company !== (initialData.company || '') ||
            startDate !== (initialData.startDate || '') ||
            endDate !== (initialData.endDate || '') ||
            isCurrentPosition !== (initialData.isCurrentPosition || false) ||
            description !== (initialData.description || '');
    };

    const openSheet = () => {
        translateY.setValue(0);
        setShowUndoSheet(true);
    };

    const closeSheet = () => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 200,
            useNativeDriver: true,
        }).start(() => {
            setShowUndoSheet(false);
            translateY.setValue(0);
        });
    };

    const handleBack = () => {
        if (hasChanges()) {
            Keyboard.dismiss();
            openSheet();
        } else {
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Go back');
            }
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
        if (navigation?.goBack) {
            navigation.goBack();
        } else {
            console.log('Saved and go back');
        }
    };

    const handleContinueFilling = () => {
        closeSheet();
    };

    const handleUndoChanges = () => {
        closeSheet();
        setTimeout(() => {
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Undo and go back');
            }
        }, 250);
    };

    const handleRemove = () => {
        // TODO: Gọi API xóa work experience
        console.log('Removing work experience:', initialData.id);
        if (navigation?.goBack) {
            navigation.goBack();
        } else {
            console.log('Removed and go back');
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.keyboardView}
            >
                <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                    <View style={styles.content}>
                        {!showUndoSheet && (
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
                        )}
                        {showUndoSheet && <View style={styles.backButtonPlaceholder}/>}

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

                            {/* Checkbox */}
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

                            {/* Description */}
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
                                    onPress={handleRemove}
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

            <Modal
                visible={showUndoSheet}
                animationType="slide"
                transparent={true}
                onRequestClose={closeSheet}
            >
                <TouchableWithoutFeedback onPress={closeSheet}>
                    <View style={styles.modalOverlay}>
                        {/* Header trong modal */}
                        <SafeAreaView edges={['top']} style={styles.modalHeader}>
                            <TouchableOpacity onPress={closeSheet} style={styles.closeButton}>
                                <MaterialCommunityIcons name="close" size={28} color="#FFF"/>
                            </TouchableOpacity>
                        </SafeAreaView>

                        <TouchableWithoutFeedback>
                            <Animated.View
                                style={[
                                    styles.bottomSheet,
                                    {transform: [{translateY}]}
                                ]}
                            >
                                <View
                                    style={styles.handleBarContainer}
                                    {...panResponder.panHandlers}
                                >
                                    <View style={styles.sheetHandle}/>
                                </View>

                                <CustomText style={styles.sheetTitle}>Undo Changes ?</CustomText>
                                <CustomText style={styles.sheetSubtitle}>
                                    Are you sure you want to change what you entered?
                                </CustomText>

                                <TouchableOpacity
                                    style={styles.continueButton}
                                    onPress={handleContinueFilling}
                                    activeOpacity={0.8}
                                >
                                    <CustomText style={styles.continueButtonText}>CONTINUE FILLING</CustomText>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={styles.undoButton}
                                    onPress={handleUndoChanges}
                                    activeOpacity={0.8}
                                >
                                    <CustomText style={styles.undoButtonText}>UNDO CHANGES</CustomText>
                                </TouchableOpacity>
                            </Animated.View>
                        </TouchableWithoutFeedback>
                    </View>
                </TouchableWithoutFeedback>
            </Modal>
        </SafeAreaView>
    );
};

export default AddWorkExperience;