import React, {useMemo, useState} from 'react';
import {View, TouchableOpacity, StyleSheet, Image, Alert} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import AsyncStorage from "@react-native-async-storage/async-storage";
import CustomText from '../../components/common/CustomText';
import CustomHeader from '../../components/common/CustomHeader';
import LevelPickerModal from './LevelPickerModal';
import {authApis, endpoints} from "../../utils/Apis";

const LanguageDetail = ({navigation, route}) => {
    const langFromRoute = route?.params?.language;
    const isAddMode = route?.params?.isAdd;
    const [loading, setLoading] = useState(false);

    const [lang, setLang] = useState(() => ({
        ...langFromRoute,
        isFirst: !!langFromRoute?.is_first_language || !!langFromRoute?.isFirst,
        oral: (typeof langFromRoute?.oral_level === 'number' ? langFromRoute.oral_level : langFromRoute?.oral) || 0,
        written: (typeof langFromRoute?.written_level === 'number' ? langFromRoute.written_level : langFromRoute?.written) || 0,
        name: langFromRoute?.name || langFromRoute?.language || "",
        flag: langFromRoute?.flag
    }));

    const [picker, setPicker] = useState({visible: false, field: 'oral'});

    const subtitle = useMemo(
        () => 'Proficiency level: 0 - Poor, 10 - Very good',
        []
    );

    const openPicker = (field) => setPicker({visible: true, field});
    const closePicker = () => setPicker((p) => ({...p, visible: false}));

    const onPickLevel = (level) => {
        setLang((prev) => ({...prev, [picker.field]: level}));
    };

    const onSave = async () => {
        if (lang.oral === 0 && lang.written === 0) {
            Alert.alert("Lưu ý", "Vui lòng chọn trình độ ngôn ngữ.");
            return;
        }

        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');

            const payload = {
                language: lang.name,
                oral_level: lang.oral,
                written_level: lang.written,
                is_first_language: lang.isFirst
            };

            console.log("Sending to Backend:", payload);

            if (isAddMode) {
                await authApis(token).post(endpoints.languages, payload);
            } else {
                if (langFromRoute?.id) {
                    await authApis(token).patch(`${endpoints.languages}${langFromRoute.id}/`, payload);
                }
            }

            if (route?.params?.onSave) {
                route.params.onSave();
            }

            if (isAddMode) {
                navigation.pop(2);
            } else {
                navigation.goBack();
            }

        } catch (error) {
            console.error("Lỗi API:", error);
            Alert.alert("Lỗi", "Không thể lưu thay đổi. Vui lòng thử lại.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <CustomHeader navigation={navigation} title=""/>
            <View style={styles.content}>
                <View style={styles.titleWrap}>
                    <CustomText style={styles.title}>Add Language</CustomText>
                </View>

                <View style={styles.card}>
                    <View style={styles.row}>
                        <CustomText style={styles.label}>Language</CustomText>
                        <View style={styles.rightLang}>
                            <View style={styles.flagWrap}>
                                <Image source={{uri: lang.flag}} style={styles.flagImg}/>
                            </View>
                            <CustomText style={styles.value}>{lang.name}</CustomText>
                        </View>
                    </View>

                    <View style={styles.divider}/>

                    {/* First language row */}
                    <TouchableOpacity
                        activeOpacity={0.9}
                        onPress={() => setLang((p) => ({...p, isFirst: !p.isFirst}))}
                        style={styles.row}
                    >
                        <CustomText style={styles.label}>First language</CustomText>
                        <MaterialCommunityIcons
                            name={lang.isFirst ? 'radiobox-marked' : 'radiobox-blank'}
                            size={22}
                            color={lang.isFirst ? '#FF8A00' : '#CFCFDB'}
                        />
                    </TouchableOpacity>
                </View>

                <View style={styles.card}>
                    <TouchableOpacity activeOpacity={0.9} onPress={() => openPicker('oral')}>
                        <CustomText style={styles.sectionTitle}>Oral</CustomText>
                        {lang.written > 0 ? (
                            <CustomText style={styles.sectionValue}>level {lang.oral}</CustomText>
                        ) : (
                            <CustomText style={styles.sectionValue}>Choose your oral skill level</CustomText>
                        )}
                    </TouchableOpacity>

                    <View style={styles.divider}/>

                    <TouchableOpacity activeOpacity={0.9} onPress={() => openPicker('written')}>
                        <CustomText style={styles.sectionTitle}>Written</CustomText>
                        {lang.written > 0 ? (
                            <CustomText style={styles.sectionValue}>level {lang.written}</CustomText>
                        ) : (
                            <CustomText style={styles.sectionValue}>Choose your writing skill level</CustomText>
                        )}
                    </TouchableOpacity>
                </View>

                <CustomText style={styles.subnote}>{subtitle}</CustomText>
            </View>

            <View style={styles.footer}>
                <TouchableOpacity activeOpacity={0.9} style={styles.saveBtn} onPress={onSave}>
                    <CustomText style={styles.saveText}>SAVE</CustomText>
                </TouchableOpacity>
            </View>

            <LevelPickerModal
                visible={picker.visible}
                title={picker.field === 'oral' ? 'Oral' : 'Written'}
                selectedLevel={picker.field === 'oral' ? lang.oral : lang.written}
                onClose={closePicker}
                onDone={(level) => {
                    setLang(prev => ({...prev, [picker.field]: level}));
                    closePicker();
                }}
            />


        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9'
    },

    titleWrap: {
        paddingHorizontal: 18,
        paddingTop: 6,
        paddingBottom: 10
    },
    title: {
        fontSize: 22,
        fontWeight: '800',
        color: '#150B3D'
    },

    card: {
        marginHorizontal: 18,
        marginTop: 12,
        backgroundColor: '#FFFFFF',
        borderRadius: 18,
        paddingHorizontal: 16,
        paddingVertical: 10,
        elevation: 1,
    },

    row: {
        paddingVertical: 14,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    divider: {
        height: 1,
        backgroundColor: '#DEE1E7',
        marginBottom: 10
    },

    label: {
        fontSize: 16,
        fontWeight: '700',
        color: '#150B3D'
    },
    value: {
        fontSize: 14.5,
        fontWeight: '700',
        color: '#150B3D'
    },

    rightLang: {
        flexDirection: 'row',
        alignItems: 'center'
    },

    flagWrap: {
        width: 35,
        height: 35,
        borderRadius: 15,
        overflow: 'hidden',
        marginRight: 10,
        borderWidth: 1,
        borderColor: '#EFEFF5',
    }
    ,
    flagImg: {
        width: '100%',
        height: '100%'
    },

    sectionTitle: {
        marginTop: 10,
        fontSize: 16,
        fontWeight: '800',
        color: '#150B3D'
    },
    sectionValue: {
        marginTop: 12,
        fontSize: 15,
        color: '#B2B2BD',
        fontWeight: '400',
        marginBottom: 10,
        marginLeft: 0,
    },

    subnote: {
        marginHorizontal: 18,
        marginTop: 16,
        fontSize: 15,
        color: '#B2B2BD',
        fontWeight: '400',
        marginLeft: 23,
    },

    saveBtn: {
        marginHorizontal: 60,
        marginTop: 28,
        height: 52,
        borderRadius: 10,
        backgroundColor: '#130160',
        alignItems: 'center',
        justifyContent: 'center',
    },
    saveText: {
        color: '#FFFFFF',
        fontWeight: '800',
        fontSize: 16
    },
    footer: {
        position: 'absolute',
        left: 18,
        right: 18,
        bottom: 35,
    },
    content: {
        flex: 1,
        paddingBottom: 90,
    }
});

export default LanguageDetail;
