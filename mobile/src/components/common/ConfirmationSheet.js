import React, {useRef, useEffect} from 'react';
import {
    View,
    StyleSheet,
    Modal,
    Dimensions,
    TouchableOpacity,
    TouchableWithoutFeedback,
    PanResponder,
    Animated
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from './CustomText';

const {height: screenHeight} = Dimensions.get('window');

const ConfirmationSheet = ({
                               visible,
                               onClose,
                               onConfirm,
                               type = 'undo'
                           }) => {
    const translateY = useRef(new Animated.Value(screenHeight)).current;

    const config =
        type === 'remove_appreciation'
            ? {
                title: 'Remove Appreciation ?',
                subtitle: 'Are you sure you want to remove this award?',
                primaryBtnText: 'CONTINUE FILLING',
                secondaryBtnText: 'UNDO CHANGES',
                secondaryBtnColor: '#D6CDFE',
                secondaryTextColor: '#FFF',
            }
            : type === 'remove_language'
                ? {
                    title: `Remove Language} ?`,
                    subtitle: 'Are you sure you want to delete this language?',
                    primaryBtnText: 'CONTINUE FILLING',
                    secondaryBtnText: 'UNDO CHANGES',
                    secondaryBtnColor: '#D6CDFE',
                    secondaryTextColor: '#FFF',
                }
                : type === 'remove'
                    ? {
                        title: 'Remove Work Experience?',
                        subtitle: 'Are you sure you want to remove this experience permanently?',
                        primaryBtnText: 'CANCEL',
                        secondaryBtnText: 'YES, REMOVE',
                        secondaryBtnColor: '#FF4B55',
                        secondaryTextColor: '#FFF',
                    }
                    : {
                        title: 'Undo Changes ?',
                        subtitle: 'Are you sure you want to change what you entered?',
                        primaryBtnText: 'CONTINUE FILLING',
                        secondaryBtnText: 'UNDO CHANGES',
                        secondaryBtnColor: '#D6CDFE',
                        secondaryTextColor: '#FFF',
                    };


    useEffect(() => {
        if (visible) {
            openSheet();
        } else {
            closeSheet();
        }
    }, [visible]);

    const openSheet = () => {
        Animated.spring(translateY, {
            toValue: 0,
            useNativeDriver: true,
            tension: 65,
            friction: 11
        }).start();
    };

    const closeSheet = () => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 200,
            useNativeDriver: true,
        }).start();
    };

    const handleClosePress = () => {
        closeSheet();
        setTimeout(() => {
            onClose();
        }, 200);
    };

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
                    handleClosePress();
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

    if (!visible) return null;

    return (
        <Modal
            visible={visible}
            animationType="fade"
            transparent={true}
            onRequestClose={handleClosePress}
        >
            <TouchableWithoutFeedback onPress={handleClosePress}>
                <View style={styles.modalOverlay}>
                    <SafeAreaView edges={['top']} style={styles.modalHeader}>
                        <TouchableOpacity onPress={handleClosePress} style={styles.closeButton}>
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

                            <CustomText style={styles.sheetTitle}>{config.title}</CustomText>
                            <CustomText style={styles.sheetSubtitle}>
                                {config.subtitle}
                            </CustomText>

                            <TouchableOpacity
                                style={styles.primaryButton}
                                onPress={handleClosePress}
                                activeOpacity={0.8}
                            >
                                <CustomText style={styles.primaryButtonText}>{config.primaryBtnText}</CustomText>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={[styles.secondaryButton, {backgroundColor: config.secondaryBtnColor}]}
                                onPress={() => {
                                    closeSheet();
                                    setTimeout(() => {
                                        onConfirm();
                                    }, 200);
                                }}
                                activeOpacity={0.8}
                            >
                                <CustomText style={[styles.secondaryButtonText, {color: config.secondaryTextColor}]}>
                                    {config.secondaryBtnText}
                                </CustomText>
                            </TouchableOpacity>
                        </Animated.View>
                    </TouchableWithoutFeedback>
                </View>
            </TouchableWithoutFeedback>
        </Modal>
    );
};

const styles = StyleSheet.create({
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'flex-end',
    },
    modalHeader: {
        flex: 1,
        paddingHorizontal: 20,
        alignItems: 'flex-end',
    },
    closeButton: {
        width: 44,
        height: 44,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: -10,
        marginTop: 10,
    },
    bottomSheet: {
        backgroundColor: '#FFF',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        paddingHorizontal: 30,
        paddingBottom: 10,
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: 'auto',
        minHeight: 270,
    },
    handleBarContainer: {
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 50,
    },
    sheetHandle: {
        width: 50,
        height: 4,
        backgroundColor: '#E0E0E0',
        borderRadius: 2,
    },
    sheetTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#150B3D',
        textAlign: 'center',
        marginBottom: 10,
        marginTop: 10,
    },
    sheetSubtitle: {
        fontSize: 13,
        color: '#524B6B',
        textAlign: 'center',
        marginBottom: 30,
    },
    primaryButton: {
        backgroundColor: '#130160',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
        marginBottom: 15,
    },
    primaryButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFF',
        letterSpacing: 1,
    },
    secondaryButton: {
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
    },
    secondaryButtonText: {
        fontSize: 15,
        fontWeight: '700',
        letterSpacing: 1,
    },
});

export default ConfirmationSheet;