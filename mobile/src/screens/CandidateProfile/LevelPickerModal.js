import React, {useEffect, useRef, useState} from 'react';
import {
    View,
    Modal,
    TouchableOpacity,
    TouchableWithoutFeedback,
    StyleSheet,
    Animated,
    PanResponder,
    Dimensions,
    ScrollView,
} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';

const {height: screenHeight} = Dimensions.get('window');
const LEVELS = Array.from({length: 11}, (_, i) => i); // 0..10

const LevelPickerModal = ({
                              visible,
                              title = 'Choose level',
                              selectedLevel = 0,
                              onDone,
                              onClose,
                          }) => {
    const [internalVisible, setInternalVisible] = useState(false);
    const [tempLevel, setTempLevel] = useState(selectedLevel);

    const translateY = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        if (visible) {
            setTempLevel(selectedLevel);
            translateY.setValue(0);
            setInternalVisible(true);
        } else {
            if (internalVisible) closeModal();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visible, selectedLevel]);

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, gesture) => {
                return Math.abs(gesture.dy) > Math.abs(gesture.dx);
            },
            onPanResponderMove: (_, gesture) => {
                if (gesture.dy > 0) translateY.setValue(gesture.dy);
            },
            onPanResponderRelease: (_, gesture) => {
                if (gesture.dy > 100) {
                    Animated.timing(translateY, {
                        toValue: screenHeight,
                        duration: 200,
                        useNativeDriver: true,
                    }).start(() => {
                        translateY.setValue(0);
                        setInternalVisible(false);
                        onClose?.();
                    });
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

    const closeModal = () => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 200,
            useNativeDriver: true,
        }).start(() => {
            translateY.setValue(0);
            setInternalVisible(false);
            onClose?.();
        });
    };

    const handleDone = () => {
        onDone?.(tempLevel);
        closeModal();
    };

    return (
        <Modal
            visible={internalVisible}
            transparent
            animationType="none"
            onRequestClose={closeModal}
        >
            <TouchableWithoutFeedback onPress={closeModal}>
                <View style={styles.overlay}>
                    <TouchableWithoutFeedback>
                        <Animated.View style={[styles.sheet, {transform: [{translateY}]}]}>
                            <View style={styles.handleBarContainer} {...panResponder.panHandlers}>
                                <View style={styles.handleBar}/>
                            </View>

                            <View style={styles.header}>
                                <CustomText style={styles.title}>{title}</CustomText>
                                <TouchableOpacity onPress={closeModal}>
                                    <MaterialCommunityIcons
                                        name="close-circle-outline"
                                        size={28}
                                        color="#AAA6B9"
                                    />
                                </TouchableOpacity>
                            </View>

                            {/* ScrollView: đây là phần fix không scroll được > level 7 */}
                            <ScrollView
                                style={{flex: 1}}
                                contentContainerStyle={styles.listContent}
                                showsVerticalScrollIndicator={false}
                            >
                                {LEVELS.map((lv) => {
                                    const active = tempLevel === lv;
                                    return (
                                        <TouchableOpacity
                                            key={lv}
                                            activeOpacity={0.85}
                                            style={[styles.item, active && styles.itemSelected]}
                                            onPress={() => setTempLevel(lv)}
                                        >
                                            <CustomText style={[styles.itemText, active && styles.itemTextSelected]}>
                                                Level {lv}
                                            </CustomText>

                                            <MaterialCommunityIcons
                                                name={active ? 'radiobox-marked' : 'radiobox-blank'}
                                                size={22}
                                                color={active ? '#FF8A00' : '#CFCFDB'}
                                            />
                                        </TouchableOpacity>
                                    );
                                })}
                            </ScrollView>

                            {/* DONE */}
                            <TouchableOpacity style={styles.doneBtn} activeOpacity={0.9} onPress={handleDone}>
                                <CustomText style={styles.doneText}>DONE</CustomText>
                            </TouchableOpacity>
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
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end',
    },
    sheet: {
        backgroundColor: '#FFFFFF',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        height: '80%',
        paddingTop: 10,
        paddingBottom: 18,
    },

    handleBarContainer: {
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 50,
    },
    handleBar: {
        width: 40,
        height: 5,
        backgroundColor: '#E0E0E0',
        borderRadius: 3,
    },

    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        marginBottom: 20,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#130160'
    },

    listContent: {
        paddingHorizontal: 20,
        paddingBottom: 20,
    },

    item: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 15,
        borderRadius: 12,
        backgroundColor: '#F9F9F9',
        borderWidth: 1,
        borderColor: 'transparent',
        marginBottom: 10,
    },
    itemSelected: {
        backgroundColor: '#F3F0FF',
        borderColor: '#130160',
    },
    itemText: {
        fontSize: 15,
        color: '#524B6B'
    },
    itemTextSelected: {
        color: '#130160',
        fontWeight: 'bold'
    },

    doneBtn: {
        marginHorizontal: 20,
        height: 54,
        borderRadius: 10,
        backgroundColor: '#120D3F',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: 8,
    },
    doneText: {
        color: '#FFFFFF',
        fontWeight: '800',
        fontSize: 16
    },
});

export default LevelPickerModal;
