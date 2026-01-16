import React, {useMemo, useRef, useState} from 'react';
import {
    View,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ScrollView,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
    Alert
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';
import MonthYearInput from "../../components/common/MonthYear/MonthYearInput";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {authApis, endpoints} from "../../utils/Apis";

const AppreciationForm = ({navigation, route}) => {
    const initial = route?.params?.appreciation || null;
    const isEdit = !!initial?.id;
    const [loading, setLoading] = useState(false);


    const parseDateString = (dateString) => {
        if (!dateString) return null;
        const date = new Date(dateString);
        return {month: date.getMonth() + 1, year: date.getFullYear()};
    };

    const initialForm = useMemo(
        () => ({
            id: initial?.id ?? null,
            awardName: initial?.title ?? '',
            category: initial?.subtitle ?? '',
            endDate: parseDateString(initial?.year),
            description: initial?.description ?? '',
        }),
        [initial]
    );


    const [form, setForm] = useState(initialForm);
    const [undoVisible, setUndoVisible] = useState(false);
    const [removeVisible, setRemoveVisible] = useState(false);

    const sameEndDate =
        (form.endDate?.month ?? null) === (initialForm.endDate?.month ?? null) &&
        (form.endDate?.year ?? null) === (initialForm.endDate?.year ?? null);

    const isDirty = useMemo(() => {
        return (
            form.awardName !== initialForm.awardName ||
            form.category !== initialForm.category ||
            !sameEndDate ||
            form.description !== initialForm.description
        );
    }, [form, initialForm, sameEndDate]);

    const onClosePress = () => {
        if (!isDirty) {
            navigation.goBack();
            return;
        }
        setUndoVisible(true);
    };

    const getMonthNumber = (month) => {
        if (!month) return null;
        if (!isNaN(month)) return String(month).padStart(2, '0');

        const months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
            'january': '01', 'february': '02', 'march': '03', 'april': '04', 'june': '06',
            'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'
        };

        const key = String(month).toLowerCase().substring(0, 3); // Lấy 3 chữ cái đầu
        return months[key] || '01'; // Fallback về 01 nếu không tìm thấy
    };

    const formatPayloadDate = (dateObj) => {
        if (!dateObj || !dateObj.year || !dateObj.month) return null;
        const year = dateObj.year;
        const month = getMonthNumber(dateObj.month);
        return `${year}-${month}-01`;
    };

    const onUndoConfirm = () => {
        setForm(initialForm);
        setUndoVisible(false);
        navigation.goBack();
    };

    const onSave = async () => {
        try {
            setLoading(true);
            const token = await AsyncStorage.getItem('token');

            const payload = {
                award_name: form.awardName,
                category: form.category,
                end_date: formatPayloadDate(form.endDate),
                description: form.description
            };

            console.log("Payload sending:", payload);

            if (!payload.award_name || !payload.category) {
                Alert.alert("Missing Info", "Please fill in Award Name and Category");
                setLoading(false);
                return;
            }

            if (isEdit) {
                await authApis(token).patch(`${endpoints.appreciations}${form.id}/`, payload);
            } else {
                await authApis(token).post(endpoints.appreciations, payload);
            }

            navigation.goBack();

        } catch (error) {
            console.error(error);
            Alert.alert("Error", "Could not save appreciation.");
        } finally {
            setLoading(false);
        }
    };

    const onRemove = async () => {
        try {
            if (!form.id) return;
            setLoading(true);
            const token = await AsyncStorage.getItem('token');

            await authApis(token).delete(`${endpoints.appreciations}${form.id}/`);

            if (route?.params?.onSelect) {
                route.params.onSelect();
            }
            setRemoveVisible(false);
            navigation.goBack();
        } catch (error) {
            console.error(error);
            Alert.alert("Error", "Could not delete.");
        } finally {
            setLoading(false);
        }
    };


    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <View style={styles.topBar}>
                <TouchableOpacity onPress={onClosePress} hitSlop={10}>
                    <MaterialCommunityIcons
                        name={isEdit ? 'close' : 'arrow-left'}
                        size={26}
                        color="#14121F"
                    />
                </TouchableOpacity>
            </View>

            <KeyboardAvoidingView
                style={{flex: 1}}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            >
                <ScrollView
                    style={{flex: 1}}
                    contentContainerStyle={styles.content}
                    showsVerticalScrollIndicator={false}
                >
                    <CustomText style={styles.title}>
                        {isEdit ? 'Edit Appreciation' : 'Add Appreciation'}
                    </CustomText>

                    {/* Award name */}
                    <CustomText style={styles.label}>Award name</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.awardName}
                            onChangeText={(t) => setForm((p) => ({...p, awardName: t}))}
                            placeholder=""
                            style={styles.input}
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    {/* Category */}
                    <CustomText style={styles.label}>Category/Achievement achieved</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.category}
                            onChangeText={(t) => setForm((p) => ({...p, category: t}))}
                            placeholder=""
                            style={styles.input}
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    {/* End date */}
                    <CustomText style={styles.label}>End date</CustomText>
                    <View style={{width: 170}}>
                        <MonthYearInput
                            label={null}
                            value={form.endDate}
                            onChange={(val) => setForm((p) => ({...p, endDate: val}))}
                            placeholder="Select Date"
                            required={false}
                        />
                    </View>

                    {/* Description */}
                    <CustomText style={styles.label}>Description</CustomText>
                    <View style={[styles.inputWrap, styles.textAreaWrap]}>
                        <TextInput
                            value={form.description}
                            onChangeText={(t) => setForm((p) => ({...p, description: t}))}
                            placeholder="Write additional information here"
                            style={[styles.input, styles.textArea]}
                            placeholderTextColor="#BDB8CC"
                            multiline
                            textAlignVertical="top"
                        />
                    </View>

                    <View style={{height: isEdit ? 120 : 90}}/>
                </ScrollView>

                {!isEdit ? (
                    <View style={styles.footerOne}>
                        <TouchableOpacity activeOpacity={0.9} style={styles.saveBtn} onPress={onSave}>
                            <CustomText style={styles.saveText}>SAVE</CustomText>
                        </TouchableOpacity>
                    </View>
                ) : (
                    <View style={styles.footerTwo}>
                        <TouchableOpacity
                            activeOpacity={0.9}
                            style={styles.removeBtn}
                            onPress={() => setRemoveVisible(true)}
                        >
                            <CustomText style={styles.removeText}>REMOVE</CustomText>
                        </TouchableOpacity>

                        <TouchableOpacity activeOpacity={0.9} style={styles.saveBtnSmall} onPress={onSave}>
                            <CustomText style={styles.saveText}>SAVE</CustomText>
                        </TouchableOpacity>
                    </View>
                )}
            </KeyboardAvoidingView>

            <ConfirmationSheet
                visible={undoVisible}
                type="undo"
                onClose={() => setUndoVisible(false)}
                onConfirm={onUndoConfirm}
            />

            <ConfirmationSheet
                visible={removeVisible}
                type="remove_appreciation"
                onClose={() => setRemoveVisible(false)}
                onConfirm={onRemove}
            />
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {flex: 1, backgroundColor: '#F6F7FB'},

    topBar: {
        paddingHorizontal: 18,
        paddingTop: 6,
        paddingBottom: 8,
        flexDirection: 'row',
        justifyContent: 'flex-start',
    },

    content: {
        paddingHorizontal: 22,
        paddingTop: 6,
    },

    title: {
        fontSize: 22,
        fontWeight: '600',
        color: '#150A33',
        marginBottom: 22,
        marginLeft: 5
    },

    label: {
        fontSize: 15,
        fontWeight: '500',
        color: '#150A33',
        marginBottom: 10,
        marginTop: 14,
        marginLeft: 5

    },

    inputWrap: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 12,
        borderWidth: 1,
        borderColor: '#ECEAF4',
    },

    input: {
        fontSize: 15,
        color: '#524B6B',
        fontWeight: '400',
        padding: 0,
    },

    textAreaWrap: {
        height: 170
    },
    textArea: {
        height: 170
    },

    footerOne: {
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: 25,
    },

    footerTwo: {
        position: 'absolute',
        left: 22,
        right: 22,
        bottom: 25,
        flexDirection: 'row',
        gap: 14,
    },

    saveBtn: {
        height: 54,
        borderRadius: 12,
        backgroundColor: '#120D3F',
        alignItems: 'center',
        justifyContent: 'center',
    },

    saveBtnSmall: {
        flex: 1,
        height: 54,
        borderRadius: 12,
        backgroundColor: '#120D3F',
        alignItems: 'center',
        justifyContent: 'center',
    },

    saveText: {
        color: '#FFFFFF',
        fontWeight: '900',
        fontSize: 15.5,
        letterSpacing: 1,
    },

    removeBtn: {
        flex: 1,
        height: 54,
        borderRadius: 12,
        backgroundColor: '#D6CDFE',
        alignItems: 'center',
        justifyContent: 'center',
    },

    removeText: {
        color: '#FFFFFF',
        fontWeight: '900',
        fontSize: 15.5,
        letterSpacing: 1,
        opacity: 0.9,
    },
    loadingOverlay: {
        position: 'absolute',
        zIndex: 999,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255,255,255,0.5)',
        justifyContent: 'center',
        alignItems: 'center'
    }
});

export default AppreciationForm;
