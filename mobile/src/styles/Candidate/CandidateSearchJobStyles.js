import {StyleSheet} from "react-native";

export default StyleSheet.create({
    container: {
        backgroundColor: "#F9F9F9",
        flex: 1
    },
    headerContainer: {
        height: 250,
        width: '100%',
        borderBottomLeftRadius: 30,
        borderBottomRightRadius: 30,
        overflow: 'hidden',
        position: 'relative',
    },
    bg: {
        position: 'absolute',
        top: -20,
        left: 0,
        right: 0,
        bottom: 0,
    },
    searchContent: {
        paddingHorizontal: 20,
        marginTop: 10,
    },
    searchBoxContainer: {
        gap: 15
    },
    inputWrapper: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'white',
        borderRadius: 15,
        paddingHorizontal: 15,
        height: 50,
    },
    textInput: {
        flex: 1,
        marginLeft: 10,
        fontSize: 14,
        color: '#0D0140',
        fontFamily: 'DMSans-Regular',
    },
    filterBar: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 10,
        paddingLeft: 15,
    },
    filterIconBtn: {
        backgroundColor: '#130160',
        width: 40,
        height: 40,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 10,
    },
    chipScroll: {
        flex: 1
    },
    chipBtn: {
        backgroundColor: '#F2F2F3',
        paddingHorizontal: 15,
        paddingVertical: 10,
        borderRadius: 10,
        marginRight: 10,
    },
    chipText: {
        color: '#524B6B',
        fontSize: 13
    },
    listContent: {
        paddingHorizontal: 20,
        paddingBottom: 20
    },
})