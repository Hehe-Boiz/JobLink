import React, {useState, useRef, useEffect, useCallback} from 'react';
import {View, TouchableOpacity, ScrollView, PanResponder} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import CustomFooter from '../../components/common/CustomFooter';
import CustomSelector from '../../components/common/CustomSelector';
import styles from '../../styles/Candidate/CandidateSearchAdvanceStyles';

const CATEGORIES = [
    {id: '1', name: 'Design'},
    {id: '2', name: 'Finance'},
    {id: '3', name: 'Technology'},
    {id: '4', name: 'Marketing'},
];

const SUB_CATEGORIES = [
    {id: '1', name: 'UI/UX Design'},
    {id: '2', name: 'Graphic Design'},
    {id: '3', name: 'Motion Design'},
    {id: '4', name: 'Web Design'},
];

const LOCATIONS = [
    {id: '1', name: 'California, USA'},
    {id: '2', name: 'New York, USA'},
    {id: '3', name: 'Hanoi, Vietnam'},
    {id: '4', name: 'Ho Chi Minh'},
];

const JOB_TYPES = [
    {id: 'full', label: 'Full time'},
    {id: 'part', label: 'Part time'},
    {id: 'remote', label: 'Remote'},
    {id: 'contract', label: 'Contract'},
];

// --- RANGE SLIDER ĐÃ FIX ---
const RangeSlider = ({min = 0, max = 50, initialLow = 10, initialHigh = 40, onValuesChange}) => {
    const [sliderWidth, setSliderWidth] = useState(0);
    const [low, setLow] = useState(initialLow);
    const [high, setHigh] = useState(initialHigh);

    const lowRef = useRef(low);
    const highRef = useRef(high);
    const sliderWidthRef = useRef(sliderWidth);
    const startLowRef = useRef(0);
    const startHighRef = useRef(0);

    useEffect(() => {
        lowRef.current = low;
    }, [low]);

    useEffect(() => {
        highRef.current = high;
    }, [high]);

    useEffect(() => {
        sliderWidthRef.current = sliderWidth;
    }, [sliderWidth]);

    const panLow = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: () => true,
            onPanResponderGrant: () => {
                startLowRef.current = lowRef.current;
            },
            onPanResponderMove: (_, gesture) => {
                const width = sliderWidthRef.current;
                if (!width) return;

                const diff = (gesture.dx / width) * (max - min);
                let newVal = startLowRef.current + diff;
                newVal = Math.max(min, Math.min(newVal, highRef.current - 2));
                const roundedVal = Math.round(newVal);

                if (roundedVal !== lowRef.current) {
                    setLow(roundedVal);
                    onValuesChange && onValuesChange(roundedVal, highRef.current);
                }
            },
            onPanResponderRelease: () => {
                startLowRef.current = lowRef.current;
            },
        })
    ).current;

    const panHigh = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: () => true,
            onPanResponderGrant: () => {
                startHighRef.current = highRef.current;
            },
            onPanResponderMove: (_, gesture) => {
                const width = sliderWidthRef.current;
                if (!width) return;

                const diff = (gesture.dx / width) * (max - min);
                let newVal = startHighRef.current + diff;
                newVal = Math.max(lowRef.current + 2, Math.min(newVal, max));
                const roundedVal = Math.round(newVal);

                if (roundedVal !== highRef.current) {
                    setHigh(roundedVal);
                    onValuesChange && onValuesChange(lowRef.current, roundedVal);
                }
            },
            onPanResponderRelease: () => {
                startHighRef.current = highRef.current;
            },
        })
    ).current;

    const lowPos = sliderWidth ? ((low - min) / (max - min)) * sliderWidth : 0;
    const highPos = sliderWidth ? ((high - min) / (max - min)) * sliderWidth : 0;

    return (
        <View
            style={styles.sliderContainer}
            onLayout={(e) => setSliderWidth(e.nativeEvent.layout.width)}
        >
            <View style={styles.trackBg}/>

            <View
                style={[
                    styles.trackActive,
                    {left: lowPos, width: Math.max(0, highPos - lowPos)}
                ]}
            />

            <View
                style={[styles.thumb, {left: lowPos - 14}]}
                {...panLow.panHandlers}
            />

            <View
                style={[styles.thumb, {left: highPos - 14}]}
                {...panHigh.panHandlers}
            />

            <View style={[styles.priceLabel, {left: lowPos - 20}]}>
                <CustomText style={styles.priceText}>${low}k</CustomText>
            </View>
            <View style={[styles.priceLabel, {left: highPos - 20}]}>
                <CustomText style={styles.priceText}>${high}k</CustomText>
            </View>
        </View>
    );
};


const CandidateSearchAdvance = ({navigation}) => {
    const [category, setCategory] = useState(null);
    const [subCategory, setSubCategory] = useState(null);
    const [location, setLocation] = useState(null);
    const [salary, setSalary] = useState({min: 10, max: 40});
    const [selectedJobTypes, setSelectedJobTypes] = useState(['full', 'remote']);

    const toggleJobType = (id) => {
        if (selectedJobTypes.includes(id)) {
            setSelectedJobTypes(prev => prev.filter(item => item !== id));
        } else {
            setSelectedJobTypes(prev => [...prev, id]);
        }
    };

    const handleApply = () => {
        console.log("Apply:", {category, subCategory, location, salary, selectedJobTypes});
        navigation.goBack();
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>

            <View style={{paddingHorizontal: 20}}>
                <View style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingVertical: 10
                }}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#130160"/>
                    </TouchableOpacity>
                    <CustomText style={styles.headerTitle}>Filter</CustomText>
                    <View style={{width: 24}}/>
                </View>
            </View>

            <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>

                <View style={styles.sectionWrapper}>
                    <CustomSelector
                        label="Category"
                        placeholder="Select Category"
                        data={CATEGORIES}
                        selectedValue={category}
                        onSelect={setCategory}
                    />
                </View>

                <View style={styles.sectionWrapper}>
                    <CustomSelector
                        label="Sub Category"
                        placeholder="Select Sub Category"
                        data={SUB_CATEGORIES}
                        selectedValue={subCategory}
                        onSelect={setSubCategory}
                    />
                </View>

                <View style={styles.sectionWrapper}>
                    <CustomSelector
                        label="Location"
                        placeholder="Select Location"
                        data={LOCATIONS}
                        selectedValue={location}
                        onSelect={setLocation}
                    />
                </View>

                <View style={styles.sectionWrapper}>
                    <CustomText style={styles.sectionTitle}>Salary</CustomText>
                    <RangeSlider
                        min={0}
                        max={50}
                        initialLow={salary.min}
                        initialHigh={salary.max}
                        onValuesChange={(min, max) => setSalary({min, max})}
                    />
                    <View style={{height: 5}}/>
                </View>

                <View style={styles.sectionWrapper}>
                    <CustomText style={styles.sectionTitle}>Job Type</CustomText>
                    <View style={styles.chipContainer}>
                        {JOB_TYPES.map((type) => {
                            const isSelected = selectedJobTypes.includes(type.id);
                            return (
                                <TouchableOpacity
                                    key={type.id}
                                    style={[styles.chipBtn, isSelected && styles.chipBtnSelected]}
                                    onPress={() => toggleJobType(type.id)}
                                >
                                    <CustomText style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                                        {type.label}
                                    </CustomText>
                                </TouchableOpacity>
                            )
                        })}
                    </View>
                </View>

            </ScrollView>

            <CustomFooter applyTitle="APPLY NOW" onApply={handleApply}/>
        </SafeAreaView>
    );
};

export default CandidateSearchAdvance;