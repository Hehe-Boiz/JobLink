import React, {useMemo, useRef, useState} from 'react';
import {
    View,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ScrollView,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';
import MonthYearInput from "../../components/common/MonthYearInput";

const AppreciationForm = ({navigation, route}) => {
    const initial = route?.params?.data || null;
    const isEdit = !!initial?.id;

    const initialForm = useMemo(
        () => ({
            id: initial?.id ?? null,
            awardName: initial?.awardName ?? '',
            category: initial?.category ?? '',
            endDate: initial?.endDate ?? null,
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

    const onUndoConfirm = () => {
        setForm(initialForm);
        setUndoVisible(false);
        navigation.goBack();
    };

    const onSave = () => {
        const onSaveCb = route?.params?.onSave;
        if (onSaveCb) onSaveCb(form);
        navigation.goBack();
    };

    const onRemove = () => {
        const onRemoveCb = route?.params?.onRemove;
        if (onRemoveCb && form.id) onRemoveCb(form.id);
        setRemoveVisible(false);
        navigation.goBack();
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
});

export default AppreciationForm;
