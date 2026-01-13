// src/screens/Candidate/Profile/EditProfile.js
import React, {useState} from 'react';
import {
    View,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ScrollView,
    Image,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import BgHeader from '../../../assets/images/Background_1.svg';
import CustomSelector from "../../components/common/CustomSelector";
import DayMonthYearInput from "../../components/common/DayMonthYear/DayMonthYearInput";

const PHONE_CODES = [
    {id: 1, name: '+1 (US/CA)', code: '+1'},
    {id: 2, name: '+84 (VN)', code: '+84'},
    {id: 3, name: '+81 (JP)', code: '+81'},
    {id: 4, name: '+82 (KR)', code: '+82'},
    {id: 5, name: '+65 (SG)', code: '+65'},
];


const EditProfile = ({navigation, route}) => {
    const initial = route?.params?.data || {};

    const [form, setForm] = useState({
        fullName: initial.fullName ?? 'Brandone Louis',
        dob: initial.dob ?? '06 August 1992',
        gender: initial.gender ?? 'male', // 'male' | 'female'
        email: initial.email ?? 'Brandonelouis@gmail.com',
        phoneCode: initial.phoneCode ?? '+1',
        phone: initial.phone ?? '619 3456 7890',
        location: initial.location ?? 'California, United states',
        avatar: initial.avatar ?? 'https://i.pravatar.cc/150?img=12', // demo
    });

    const [phoneCodeItem, setPhoneCodeItem] = useState(() => {
        // map từ form.phoneCode (string) sang item object
        const found = PHONE_CODES.find(x => x.code === (initial.phoneCode ?? '+1'));
        return found ? {id: found.id, name: found.name} : {id: 1, name: '+1 (US/CA)'};
    });

    const [dob, setDob] = useState({day: '06', month: 'Aug', year: 1992});

    const onSave = () => {
        route?.params?.onSave?.(form);
        navigation.goBack();
    };

    const onPickDob = () => {
        // TODO: mở DatePicker modal của bạn
    };

    const onChangeImage = () => {
        // TODO: mở ImagePicker của bạn
    };

    return (
        <SafeAreaView style={styles.container} edges={['left', 'right']}>
            {/* Header BG giống CandidateProfile */}
            <View style={styles.headerContainer}>
                <BgHeader
                    width="100%"
                    height="400"
                    style={styles.bg}
                    preserveAspectRatio="none"
                />

                {/* SafeArea để ăn padding status bar đúng */}
                <SafeAreaView edges={['top']} style={styles.headerSafe}>
                    {/* Back */}
                    <TouchableOpacity
                        onPress={() => navigation.goBack()}
                        style={styles.backBtn}
                        hitSlop={10}
                        activeOpacity={0.9}
                    >
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#FFF"/>
                    </TouchableOpacity>

                    {/* Right icons */}
                    <View style={styles.rightIcons}>
                        <TouchableOpacity hitSlop={10} activeOpacity={0.9} style={styles.iconBtn}>
                            <MaterialCommunityIcons
                                name="share-variant-outline"
                                size={24}
                                color="#FFF"
                            />
                        </TouchableOpacity>
                        <TouchableOpacity hitSlop={10} activeOpacity={0.9} style={styles.iconBtn}>
                            <MaterialCommunityIcons name="cog-outline" size={24} color="#FFF"/>
                        </TouchableOpacity>
                    </View>

                    {/* ===== Profile block ===== */}
                    <View style={styles.profileBlock}>
                        {/* Avatar ở trên */}
                        <Image source={{uri: form.avatar}} style={styles.avatar}/>

                        {/* Row: text trái (2 dòng) + button phải (canh giữa theo chiều dọc) */}
                        <View style={styles.infoRow}>
                            <View style={styles.textCol}>
                                <CustomText style={styles.name}>Orlando Diggs</CustomText>
                                <CustomText style={styles.locationText}>California, USA</CustomText>
                            </View>

                            <TouchableOpacity
                                activeOpacity={0.85}
                                style={styles.changeImgBtn}
                                onPress={onChangeImage}
                            >
                                <CustomText style={styles.changeImgText}>Change image</CustomText>
                            </TouchableOpacity>
                        </View>
                    </View>
                </SafeAreaView>
            </View>

            <KeyboardAvoidingView
                style={{flex: 1}}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            >
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={styles.content}
                >
                    {/* Fullname */}
                    <CustomText style={styles.label}>Fullname</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.fullName}
                            onChangeText={(t) => setForm((p) => ({...p, fullName: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    {/* Date of birth */}
                    <CustomText style={styles.label}>Date of birth</CustomText>
                    <DayMonthYearInput
                        label={null}
                        value={dob} // { day, month, year }
                        placeholder="Select Date of birth"
                        onChange={(v) => {
                            // v = { day:'06', month:'Aug', year:1992 }
                            setDob(v);
                            setForm((p) => ({...p, dob: `${v.day} ${v.month} ${v.year}`}));
                        }}
                    />

                    {/* Gender */}
                    <CustomText style={styles.label}>Gender</CustomText>
                    <View style={styles.genderRow}>
                        <TouchableOpacity
                            activeOpacity={0.9}
                            style={styles.genderBox}
                            onPress={() => setForm((p) => ({...p, gender: 'male'}))}
                        >
                            <MaterialCommunityIcons
                                name={form.gender === 'male' ? 'radiobox-marked' : 'radiobox-blank'}
                                size={20}
                                color={form.gender === 'male' ? '#FF8A00' : '#CFCFDB'}
                            />
                            <CustomText style={styles.genderText}>Male</CustomText>
                        </TouchableOpacity>

                        <TouchableOpacity
                            activeOpacity={0.9}
                            style={styles.genderBox}
                            onPress={() => setForm((p) => ({...p, gender: 'female'}))}
                        >
                            <MaterialCommunityIcons
                                name={form.gender === 'female' ? 'radiobox-marked' : 'radiobox-blank'}
                                size={20}
                                color={form.gender === 'female' ? '#FF8A00' : '#CFCFDB'}
                            />
                            <CustomText style={styles.genderText}>Female</CustomText>
                        </TouchableOpacity>
                    </View>

                    {/* Email */}
                    <CustomText style={styles.label}>Email address</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.email}
                            onChangeText={(t) => setForm((p) => ({...p, email: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                            keyboardType="email-address"
                        />
                    </View>

                    {/* Phone */}
                    <CustomText style={styles.label}>Phone number</CustomText>
                    <View style={styles.phoneRow}>
                        <View style={{width: 130, marginTop: 5}}>
                            <CustomSelector
                                label={null}
                                placeholder="+Code"
                                data={PHONE_CODES.map(x => ({id: x.id, name: x.name}))}
                                selectedValue={phoneCodeItem}
                                onSelect={(item) => {
                                    setPhoneCodeItem(item);
                                    const picked = PHONE_CODES.find(x => x.id === item?.id);
                                    setForm(p => ({...p, phoneCode: picked?.code ?? p.phoneCode}));
                                }}
                            />
                        </View>


                        <View style={[styles.inputWrap, {flex: 1, marginTop: 0}]}>
                            <TextInput
                                value={form.phone}
                                onChangeText={(t) => setForm((p) => ({...p, phone: t}))}
                                style={styles.input}
                                placeholder=""
                                placeholderTextColor="#BDB8CC"
                                keyboardType="phone-pad"
                            />
                        </View>
                    </View>

                    {/* Location */}
                    <CustomText style={styles.label}>Location</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.location}
                            onChangeText={(t) => setForm((p) => ({...p, location: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    <View style={{height: 140}}/>
                </ScrollView>

                {/* SAVE fixed bottom */}
                <View style={styles.footer}>
                    <TouchableOpacity activeOpacity={0.9} style={styles.saveBtn} onPress={onSave}>
                        <CustomText style={styles.saveText}>SAVE</CustomText>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F6F7FB'
    },

    headerContainer: {
        height: 240,
        width: '100%',
        borderBottomLeftRadius: 22,
        borderBottomRightRadius: 22,
        overflow: 'hidden',
    },
    bg: {
        position: 'absolute',
        top: -30,
        left: 0,
        right: 0,
        bottom: 0,
    },

    headerSafe: {
        flex: 1
    },

    rightIcons: {
        position: 'absolute',
        right: 16,
        top: 40,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 14,
        zIndex: 5,
    },
    backBtn: {
        position: 'absolute',
        left: 13,
        top: 38,
        padding: 8,
        zIndex: 10,
    },
    iconBtn: {
        padding: 8
    },

    profileBlock: {
        position: 'absolute',
        left: 18,
        right: 18,
        bottom: 30,
        alignItems: 'flex-start',
        marginLeft: 15,
    },

    avatar: {
        width: 58,
        height: 58,
        borderRadius: 29,
        borderWidth: 2,
        borderColor: 'rgba(255,255,255,0.25)',
        marginBottom: 10,
    },

    // Row dưới avatar: text trái, button phải
    infoRow: {
        width: '100%',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 10,
    },

    textCol: {
        flexShrink: 1,
        minWidth: 0,
        paddingRight: 12,
    },

    name: {
        color: '#FFF',
        fontWeight: '800',
        fontSize: 18
    },
    locationText: {
        color: 'rgba(255,255,255,0.75)',
        fontWeight: '600',
        fontSize: 12,
        marginTop: 4,
    },

    changeImgBtn: {
        backgroundColor: 'rgba(255,255,255,0.16)',
        paddingVertical: 11,
        paddingHorizontal: 16,
        borderRadius: 8,
    },
    changeImgText: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: '500'
    },

    content: {
        paddingHorizontal: 22,
        paddingTop: 16
    },

    label: {
        fontSize: 16,
        fontWeight: '600',
        color: '#150A33',
        marginBottom: 10,
        marginTop: 14,
    },

    inputWrap: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 16,
        borderWidth: 1,
        borderColor: '#ECEAF4',
        height: 57,
        marginBottom: 5
    },

    inputWrapRow: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 12,
        borderWidth: 1,
        borderColor: '#ECEAF4',
        flexDirection: 'row',
        alignItems: 'center',
    },

    input: {
        fontSize: 15,
        color: '#524B6B',
        fontWeight: '400',
        padding: 0
    },

    rightIconBtn: {
        marginLeft: 10,
        padding: 2
    },

    genderRow: {
        flexDirection: 'row',
        gap: 14
    },
    genderBox: {
        flex: 1,
        height: 48,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#ECEAF4',
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 14,
    },
    genderText: {
        marginLeft: 10,
        fontWeight: '500',
        color: '#2B2640'
    },

    phoneRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10
    },
    phoneCodeBox: {
        height: 48,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#ECEAF4',
        paddingHorizontal: 12,
        flexDirection: 'row',
        alignItems: 'center',
    },
    phoneCodeText: {
        fontWeight: '600',
        color: '#14121F',
        marginRight: 8
    },

    footer: {
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: 22
    },
    saveBtn: {
        height: 54,
        borderRadius: 12,
        backgroundColor: '#130160',
        alignItems: 'center',
        justifyContent: 'center',
    },
    saveText: {
        color: '#FFFFFF',
        fontWeight: '700',
        fontSize: 15.5,
        letterSpacing: 1
    },
});

export default EditProfile;
