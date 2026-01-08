import { StyleSheet, Dimensions } from "react-native";

const { width } = Dimensions.get('window');

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    searchContainer: {
        paddingHorizontal: 20,
        marginBottom: 20,
        marginTop: 10,
    },
    searchWrapper: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        height: 50,
        paddingHorizontal: 15,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 5,
    },
    searchInput: {
        flex: 1,
        fontSize: 14,
        color: '#130160',
        marginLeft: 10,
        fontFamily: 'DMSans-Regular',
    },

    listContent: {
        paddingHorizontal: 20,
        paddingBottom: 20,
    },
    resultCount: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#130160',
        marginBottom: 15,
        marginLeft: 5
    },

    noResultContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 40,
        marginTop: -50,
    },
    noResultImage: {
        width: 200,
        height: 200,
        marginBottom: 30,
        resizeMode: 'contain'
    },
    noResultTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#130160',
        marginBottom: 10,
        textAlign: 'center'
    },
    noResultText: {
        fontSize: 14,
        color: '#524B6B',
        textAlign: 'center',
        lineHeight: 22,
    }
});