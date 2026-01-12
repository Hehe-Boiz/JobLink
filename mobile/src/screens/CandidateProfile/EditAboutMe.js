import React, {useState, useEffect, useRef} from 'react';
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
    PanResponder,
    Animated
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/CandidateProfile/EditAboutMeStyles'

const {height: screenHeight} = Dimensions.get('window');

const EditAboutMe = ({navigation, route}) => {
    const initialValue = route?.params?.aboutMe || '';

    const [aboutText, setAboutText] = useState(initialValue);
    const [showUndoSheet, setShowUndoSheet] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

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

    useEffect(() => {
        setHasChanges(aboutText !== initialValue);
    }, [aboutText, initialValue]);

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
        if (hasChanges) {
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
        // TODO: Gọi API lưu data
        console.log('Saving about me:', aboutText);
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
        setAboutText(initialValue);
        setTimeout(() => {
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Undo and go back');
            }
        }, 250);
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

                        <CustomText style={styles.title}>About me</CustomText>

                        <View style={styles.inputContainer}>
                            <TextInput
                                style={styles.textInput}
                                placeholder="Tell me about you."
                                placeholderTextColor="#AAA6B9"
                                multiline
                                textAlignVertical="top"
                                value={aboutText}
                                onChangeText={setAboutText}
                            />
                        </View>

                        <View style={styles.spacer}/>

                        <TouchableOpacity
                            style={styles.saveButton}
                            onPress={handleSave}
                            activeOpacity={0.8}
                        >
                            <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                        </TouchableOpacity>
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


export default EditAboutMe;