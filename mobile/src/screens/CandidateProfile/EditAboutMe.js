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
    Animated,
    Alert
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/CandidateProfile/EditAboutMeStyles'
import AsyncStorage from "@react-native-async-storage/async-storage";
import {authApis, endpoints} from "../../utils/Apis";
import ConfirmationSheet from '../../components/common/ConfirmationSheet';

const {height: screenHeight} = Dimensions.get('window');

const EditAboutMe = ({navigation, route}) => {
    const initialValue = route?.params?.aboutMe || '';
    const [loading, setLoading] = useState(false);
    const [aboutText, setAboutText] = useState(initialValue);
    const [showUndoSheet, setShowUndoSheet] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);


    useEffect(() => {
        setHasChanges(aboutText !== initialValue);
    }, [aboutText, initialValue]);

    const handleContinueFilling = () => {
        setShowUndoSheet(false);
    };

    const handleUndoChanges = () => {
        setAboutText(initialValue);
        navigation.goBack();
    };

    const handleBack = () => {
        if (hasChanges) {
            Keyboard.dismiss();
            setShowUndoSheet();
        } else {
            if (navigation?.goBack) {
                navigation.goBack();
            } else {
                console.log('Go back');
            }
        }
    };

    const handleSave = async () => {
        if (!hasChanges) {
             navigation.goBack();
             return;
        }

        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            if (!token) {
                Alert.alert("Lỗi", "Vui lòng đăng nhập lại.");
                return;
            }

            console.log("Sending bio update:", aboutText);

            const response = await authApis(token).patch(endpoints.candidate_profile, {
                bio: aboutText
            });

            if (response.status === 200 || response.status === 201) {
                if (navigation?.goBack) {
                    navigation.goBack();
                }
            }
        } catch (error) {
            console.error("Lỗi cập nhật About Me:", error);
            Alert.alert("Lỗi", "Không thể cập nhật thông tin. Vui lòng thử lại.");
        } finally {
            setLoading(false);
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
                                editable={!loading}
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

            <ConfirmationSheet
                visible={showUndoSheet}
                onClose={handleContinueFilling}
                onConfirm={handleUndoChanges}
                type="undo"
            />
        </SafeAreaView>
    );
};


export default EditAboutMe;