import React, {useState, useMemo} from 'react';
import {
    View,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    TouchableWithoutFeedback,
    Keyboard,
    ScrollView, TextInput,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';
import AppInput from '../../components/common/AppInput';
import AppDatePicker from '../../components/common/AppDatePicker';
import CustomSelector from '../../components/common/CustomSelector';
import styles from '../../styles/CandidateProfile/AddWorkExperienceStyles';

const AddEducation = ({navigation, route}) => {
    const initialData = route?.params?.data || {};
    const isEdit = !!initialData.id;

    const institutionList = [
        {id: '1', name: 'University of Oxford'},
        {id: '2', name: 'Harvard University'},
        {id: '3', name: 'MIT'},
        {id: '4', name: 'Stanford University'},
        {id: '5', name: 'University of Cambridge'},
        {id: '6', name: 'National University of Singapore'},
        {id: 'OTHER_OPTION', name: 'Other / Tự nhập trường khác'}
    ];

    const [formData, setFormData] = useState({
        level: initialData.level || '',
        institution: initialData.institution || '',
        fieldOfStudy: initialData.fieldOfStudy || '',
        startDate: initialData.startDate ? new Date(initialData.startDate) : null,
        endDate: initialData.endDate ? new Date(initialData.endDate) : null,
        description: initialData.description || '',
    });

    const levelList = [
        {id: '1', name: 'High School Diploma'},
        {id: '2', name: 'Associate Degree'},
        {id: '3', name: 'Bachelor\'s Degree'},
        {id: '4', name: 'Master\'s Degree'},
        {id: '5', name: 'Ph.D.'},
        {id: 'OTHER_OPTION', name: 'Other / Tự nhập cấp bậc khác'}
    ];

    const [isCurrentPosition, setIsCurrentPosition] = useState(
        initialData.isCurrentPosition || false
    );

    const [showSheet, setShowSheet] = useState(false);
    const [sheetType, setSheetType] = useState('undo');

    const isInstitutionInList = (val) => institutionList.some(item => item.name === val);
    const [isManualInstitution, setIsManualInstitution] = useState(
        !!initialData.institution && !isInstitutionInList(initialData.institution)
    );

    const isLevelInList = (val) => levelList.some(item => item.name === val);
    const [isManualLevel, setIsManualLevel] = useState(
        !!initialData.level && !isLevelInList(initialData.level)
    );

    const handleChange = (field, value) => {
        setFormData(prev => ({...prev, [field]: value}));
    };

    const handleInstitutionSelect = (item) => {
        if (!item) {
            handleChange('institution', '');
            return;
        }
        if (item.id === 'OTHER_OPTION') {
            setIsManualInstitution(true);
            handleChange('institution', '');
        } else {
            handleChange('institution', item.name);
            setIsManualInstitution(false);
        }
    };

    const handleLevelSelect = (item) => {
        if (!item) {
            handleChange('level', '');
            return;
        }
        if (item.id === 'OTHER_OPTION') {
            setIsManualLevel(true);
            handleChange('level', '');
        } else {
            handleChange('level', item.name);
            setIsManualLevel(false);
        }
    };

    const handleToggleCurrentPosition = () => {
        const newValue = !isCurrentPosition;
        setIsCurrentPosition(newValue);

        // (Tuỳ chọn) Nếu tích vào thì clear End Date
        if (newValue) {
            handleChange('endDate', null);
        }
    };

    const checkHasChanges = () => {
        // Chuẩn hóa dữ liệu để so sánh
        const currentLevel = formData.level || '';
        const initialLevel = initialData.level || '';
        const currentInstitution = formData.institution || '';
        const initialInstitution = initialData.institution || '';

        const currentField = formData.fieldOfStudy || '';
        const initialField = initialData.fieldOfStudy || '';

        const currentDesc = formData.description || '';
        const initialDesc = initialData.description || '';

        // So sánh ngày tháng (Chuyển về timestamp hoặc string để so sánh chính xác)
        const currentStart = formData.startDate ? formData.startDate.getTime() : 0;
        const initialStart = initialData.startDate ? new Date(initialData.startDate).getTime() : 0;

        const currentEnd = formData.endDate ? formData.endDate.getTime() : 0;
        const initialEnd = initialData.endDate ? new Date(initialData.endDate).getTime() : 0;

        const currentIsPos = isCurrentPosition;
        const initialIsPos = initialData.isCurrentPosition || false;

        // Trả về true nếu CÓ BẤT KỲ trường nào khác nhau
        return (
            currentLevel !== initialLevel ||
            currentInstitution !== initialInstitution ||
            currentField !== initialField ||
            currentDesc !== initialDesc ||
            currentStart !== initialStart ||
            currentEnd !== initialEnd
        );
    };

    const handleSave = () => {
        const payload = {
            ...formData,
            isCurrentPosition,
            endDate: isCurrentPosition ? null : formData.endDate
            // Format date sang string nếu cần (ví dụ YYYY-MM-DD)
            // startDate: formData.startDate?.toISOString().split('T')[0],
        };
        console.log('Saving Education:', payload);
        navigation.goBack();
    };

    const handleBack = () => {
        if (checkHasChanges()) {
            Keyboard.dismiss();
            setSheetType('undo');
            setShowSheet(true);
        } else {
            navigation.goBack();
        }
    };

    const onConfirmAction = () => {
        setShowSheet(false);

        if (sheetType === 'undo') {
            navigation.goBack();
        } else if (sheetType === 'remove') {
            console.log('Deleting...');
            navigation.goBack();
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.keyboardView}>
                <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                    <View style={styles.content}>

                        <View style={{flexDirection: 'row', alignItems: 'center', marginTop: 10}}>
                            <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                                <MaterialCommunityIcons name="arrow-left" size={28} color="#150B3D"/>
                            </TouchableOpacity>
                            <CustomText style={[styles.title, {
                                marginBottom: 0,
                                flex: 1,
                                textAlign: 'center',
                                marginRight: 44
                            }]}>
                                {isEdit ? 'Change Education' : 'Add Education'}
                            </CustomText>
                        </View>

                        <ScrollView showsVerticalScrollIndicator={false}
                                    contentContainerStyle={[styles.scrollContent, {paddingTop: 20}]}>
                            {isManualLevel ? (
                                <View style={{marginBottom: 15}}>
                                    <View style={styles.inputGroup}>
                                        <CustomText style={styles.label}>Level of education</CustomText>
                                        <TextInput
                                            style={styles.input}
                                            value={formData.level}
                                            onChangeText={(val) => handleChange('level', val)}
                                            placeholder="Enter your level (e.g. Bachelor)"
                                            placeholderTextColor="#AAA6B9"
                                        />
                                    </View>
                                    <TouchableOpacity
                                        onPress={() => setIsManualLevel(false)}
                                        style={{alignSelf: 'flex-end', marginTop: 0}}
                                    >
                                        <CustomText
                                            style={{color: '#130160', fontSize: 13, textDecorationLine: 'underline'}}>
                                            Select from list
                                        </CustomText>
                                    </TouchableOpacity>
                                </View>
                            ) : (
                                <View style={{marginBottom: 15}}>
                                    <CustomSelector
                                        label="Level of education"
                                        placeholder="Select Level"
                                        data={levelList}
                                        selectedValue={levelList.find(i => i.name === formData.level)}
                                        onSelect={handleLevelSelect}
                                    />
                                </View>
                            )}
                            {isManualInstitution ? (
                                <View style={{marginBottom: 15}}>
                                    <View style={styles.inputGroup}>
                                        <CustomText style={styles.label}>Institution name</CustomText>
                                        <TextInput
                                            style={styles.input}
                                            value={formData.institution}
                                            onChangeText={(val) => handleChange('institution', val)}
                                            placeholder="Enter your institution name"
                                            placeholderTextColor="#AAA6B9"
                                        />
                                    </View>
                                    {/*<AppInput*/}
                                    {/*    label="Institution name"*/}
                                    {/*    value={formData.institution}*/}
                                    {/*    onChangeText={(val) => handleChange('institution', val)}*/}
                                    {/*    placeholder="Enter your institution name"*/}
                                    {/*/>*/}
                                    <TouchableOpacity
                                        onPress={() => setIsManualInstitution(false)}
                                        style={{alignSelf: 'flex-end', marginTop: 0}}
                                    >
                                        <CustomText
                                            style={{color: '#130160', fontSize: 13, textDecorationLine: 'underline'}}>
                                            Select from list
                                        </CustomText>
                                    </TouchableOpacity>
                                </View>
                            ) : (
                                <View style={{marginBottom: 15}}>
                                    <CustomSelector
                                        label="Institution name"
                                        placeholder="Select Institution"
                                        data={institutionList}
                                        selectedValue={institutionList.find(i => i.name === formData.institution)}
                                        onSelect={handleInstitutionSelect}
                                    />
                                </View>
                            )}

                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Field of study</CustomText>
                                <TextInput
                                    style={styles.input}
                                    label="Field of study"
                                    value={formData.fieldOfStudy}
                                    onChangeText={(val) => handleChange('fieldOfStudy', val)}
                                    placeholder="e.g. Information Technology"
                                />
                            </View>

                            <View style={styles.dateRow}>
                                <View style={{flex: 1}}>
                                    <AppDatePicker
                                        label="Start date"
                                        value={formData.startDate}
                                        onDateChange={(date) => handleChange('startDate', date)}
                                    />
                                </View>
                                {/*<View style={{width: 15}} />*/}
                                <View style={{flex: 1}}>
                                    {isCurrentPosition ? (
                                        <View>
                                            <CustomText style={styles.label}>End date</CustomText>
                                            <View style={[styles.input, {
                                                backgroundColor: '#F9F9F9',
                                                justifyContent: 'center'
                                            }]}>
                                                <CustomText style={styles.dateTextDisabled}>
                                                    Present
                                                </CustomText>
                                            </View>
                                        </View>
                                    ) : (
                                        <AppDatePicker
                                            label="End date"
                                            value={formData.endDate}
                                            onDateChange={(date) => handleChange('endDate', date)}
                                        />
                                    )}
                                </View>
                            </View>

                            <TouchableOpacity
                                style={styles.checkboxRow}
                                onPress={handleToggleCurrentPosition}
                                activeOpacity={0.8}
                            >
                                <View style={[styles.checkbox, isCurrentPosition && styles.checkboxChecked]}>
                                    {isCurrentPosition && (
                                        <MaterialCommunityIcons name="check" size={14} color="#FFF"/>
                                    )}
                                </View>
                                <CustomText style={styles.checkboxLabel}>This is my position now</CustomText>
                            </TouchableOpacity>

                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Description</CustomText>
                                <View style={styles.textAreaContainer}>
                                    <TextInput
                                        style={styles.textArea}
                                        value={formData.description}
                                        onChangeText={(val) => handleChange('description', val)}
                                        placeholder="Write additional information here"
                                        placeholderTextColor="#AAA6B9"
                                        multiline
                                        textAlignVertical="top"
                                    />
                                </View>
                            </View>

                        </ScrollView>

                        <View style={[styles.buttonContainer, {marginBottom: 0}]}>
                            {isEdit && (
                                <TouchableOpacity style={styles.removeButton}>
                                    <CustomText style={styles.removeButtonText}>REMOVE</CustomText>
                                </TouchableOpacity>
                            )}
                            <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
                                <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                            </TouchableOpacity>
                        </View>
                    </View>
                </TouchableWithoutFeedback>
            </KeyboardAvoidingView>

            <ConfirmationSheet
                visible={showSheet}
                type={sheetType}
                onClose={() => setShowSheet(false)}
                onConfirm={onConfirmAction}
            />
        </SafeAreaView>
    );
};

export default AddEducation;