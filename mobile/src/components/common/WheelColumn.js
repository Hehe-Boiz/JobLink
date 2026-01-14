import React, {useRef, useEffect} from 'react';
import {View, FlatList, StyleSheet} from 'react-native';
import CustomText from './CustomText';

const ITEM_HEIGHT = 50;
const VISIBLE_ITEMS = 3;
const PADDING_VERTICAL = (VISIBLE_ITEMS * ITEM_HEIGHT - ITEM_HEIGHT) / 2;

const WheelColumn = ({data, selectedIndex, onValueChange}) => {
    const flatListRef = useRef(null);

    useEffect(() => {
        if (flatListRef.current && selectedIndex >= 0) {
            setTimeout(() => {
                flatListRef.current.scrollToOffset({
                    offset: selectedIndex * ITEM_HEIGHT,
                    animated: false,
                });
            }, 100);
        }
    }, []);

    const handleScrollEnd = (event) => {
        const offsetY = event.nativeEvent.contentOffset.y;
        const index = Math.round(offsetY / ITEM_HEIGHT);

        const clampedIndex = Math.max(0, Math.min(index, data.length - 1));

        if (onValueChange) {
            onValueChange(clampedIndex);
        }
    };

    const renderItem = ({item, index}) => {
        const isSelected = index === selectedIndex;

        return (
            <View style={styles.itemContainer}>
                <CustomText
                    style={[
                        styles.itemText,
                        isSelected && styles.itemTextSelected,
                    ]}
                >
                    {item}
                </CustomText>
            </View>
        );
    };

    return (
        <View style={styles.columnContainer}>
            <View style={styles.selectionHighlight}/>

            <FlatList
                ref={flatListRef}
                data={data}
                keyExtractor={(item, index) => `${item}-${index}`}
                showsVerticalScrollIndicator={false}
                snapToInterval={ITEM_HEIGHT}
                decelerationRate="fast"
                contentContainerStyle={{paddingVertical: PADDING_VERTICAL}}
                onMomentumScrollEnd={handleScrollEnd}
                renderItem={renderItem}
                getItemLayout={(_, index) => ({
                    length: ITEM_HEIGHT,
                    offset: ITEM_HEIGHT * index,
                    index,
                })}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    columnContainer: {
        height: ITEM_HEIGHT * VISIBLE_ITEMS,
        width: 80,
        overflow: 'hidden',
        position: 'relative',
    },
    selectionHighlight: {
        position: 'absolute',
        top: ITEM_HEIGHT,
        left: 0,
        right: 0,
        height: ITEM_HEIGHT,
        backgroundColor: '#FCA34D',
        borderRadius: 14,
        zIndex: 0,
    },
    itemContainer: {
        height: ITEM_HEIGHT,
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1,
    },
    itemText: {
        fontSize: 16,
        fontWeight: '500',
        color: '#AAA6B9',
    },
    itemTextSelected: {
        color: '#FFFFFF',
        fontWeight: '700',
    },
});

export default WheelColumn;