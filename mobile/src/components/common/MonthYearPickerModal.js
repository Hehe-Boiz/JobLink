import React, {useState, useRef, useEffect} from 'react';
import {
    View,
    Modal,
    TouchableOpacity,
    TouchableWithoutFeedback,
    StyleSheet,
    Animated,
    Dimensions,
    PanResponder,
} from 'react-native';
import CustomText from './CustomText';
import WheelColumn from './WheelColumn';

const {height: SCREEN_HEIGHT} = Dimensions.get('window');

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const YEARS = Array.from({length: 50}, (_, i) => 2000 + i);

const MonthYearPickerModal = ({
                                  visible,
                                  onClose,
                                  onSave,
                                  initialValue,
                                  title = 'End Date',
                              }) => {
    const getInitialMonthIndex = () => {
        if (initialValue?.month) {
            const idx = MONTHS.indexOf(initialValue.month);
            return idx >= 0 ? idx : 7;
        }
        return 7;
    };

    const getInitialYearIndex = () => {
        if (initialValue?.year) {
            const idx = YEARS.indexOf(initialValue.year);
            return idx >= 0 ? idx : 13;
        }
        return 13;
    };

    const [selectedMonthIndex, setSelectedMonthIndex] = useState(getInitialMonthIndex());
    const [selectedYearIndex, setSelectedYearIndex] = useState(getInitialYearIndex());

    const translateY = useRef(new Animated.Value(SCREEN_HEIGHT)).current;

    useEffect(() => {
        if (visible) {
            setSelectedMonthIndex(getInitialMonthIndex());
            setSelectedYearIndex(getInitialYearIndex());

            Animated.spring(translateY, {
                toValue: 0,
                useNativeDriver: true,
                damping: 20,
                stiffness: 150,
            }).start();
        } else {
            translateY.setValue(SCREEN_HEIGHT);
        }
    }, [visible]);

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, gestureState) => gestureState.dy > 10,
            onPanResponderMove: (_, gestureState) => {
                if (gestureState.dy > 0) {
                    translateY.setValue(gestureState.dy);
                }
            },
            onPanResponderRelease: (_, gestureState) => {
                if (gestureState.dy > 100 || gestureState.vy > 0.5) {
                    handleClose();
                } else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        damping: 20,
                    }).start();
                }
            },
        })
    ).current;

    const handleClose = () => {
        Animated.timing(translateY, {
            toValue: SCREEN_HEIGHT,
            duration: 250,
            useNativeDriver: true,
        }).start(() => {
            onClose();
        });
    };

    const handleSave = () => {
        const result = {
            month: MONTHS[selectedMonthIndex],
            year: YEARS[selectedYearIndex],
        };
        onSave(result);
        handleClose();
    };

    return (
        <Modal
            visible={visible}
            transparent
            animationType="none"
            statusBarTranslucent
            onRequestClose={handleClose}
        >
            <TouchableWithoutFeedback onPress={handleClose}>
                <View style={styles.overlay}>
                    <TouchableWithoutFeedback>
                        <Animated.View
                            style={[
                                styles.modalContainer,
                                {transform: [{translateY}]},
                            ]}
                        >
                            <View {...panResponder.panHandlers} style={styles.dragHandleArea}>
                                <View style={styles.dragHandle}/>
                            </View>

                            <CustomText style={styles.title}>{title}</CustomText>

                            <View style={styles.pickersRow}>
                                <WheelColumn
                                    data={MONTHS}
                                    selectedIndex={selectedMonthIndex}
                                    onValueChange={setSelectedMonthIndex}
                                />

                                <WheelColumn
                                    data={YEARS}
                                    selectedIndex={selectedYearIndex}
                                    onValueChange={setSelectedYearIndex}
                                />
                            </View>

                            {/* Buttons */}
                            <View style={styles.buttonContainer}>
                                <TouchableOpacity
                                    style={styles.saveButton}
                                    onPress={handleSave}
                                    activeOpacity={0.8}
                                >
                                    <CustomText style={styles.saveText}>SAVE</CustomText>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={styles.cancelButton}
                                    onPress={handleClose}
                                    activeOpacity={0.8}
                                >
                                    <CustomText style={styles.cancelText}>CANCEL</CustomText>
                                </TouchableOpacity>
                            </View>
                        </Animated.View>
                    </TouchableWithoutFeedback>
                </View>
            </TouchableWithoutFeedback>
        </Modal>
    );
};

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'flex-end',
    },
    modalContainer: {
        backgroundColor: '#FFFFFF',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        paddingHorizontal: 24,
        paddingBottom: 40,
    },
    dragHandleArea: {
        alignItems: 'center',
        paddingTop: 12,
        paddingBottom: 8,
    },
    dragHandle: {
        width: 40,
        height: 4,
        backgroundColor: '#AAA6B9',
        borderRadius: 2,
    },
    title: {
        fontSize: 18,
        fontWeight: '700',
        color: '#150B3D',
        textAlign: 'center',
        marginTop: 16,
        marginBottom: 24,
    },
    pickersRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 24,
        marginBottom: 32,
    },
    buttonContainer: {
        gap: 12,
    },
    saveButton: {
        backgroundColor: '#130160',
        height: 56,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
    },
    saveText: {
        color: '#FFFFFF',
        fontWeight: '700',
        fontSize: 16,
    },
    cancelButton: {
        backgroundColor: '#D6CDFE',
        height: 56,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
    },
    cancelText: {
        color: '#FFFFFF',
        fontWeight: '700',
        fontSize: 16,
    },
});

export default MonthYearPickerModal;